import logging
import re
import time
import psycopg2
import requests
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class LinkedInPostScraper:
    def __init__(self, username, password, search_query, db_params):
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-notifications")
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        self.username = username
        self.password = password
        self.search_query = search_query
        self.db_params = db_params
        self.conn = None
        self.cursor = None

    def reset_table(self):
        try:
            self.cursor.execute("TRUNCATE TABLE posts;")
            self.cursor.execute("ALTER SEQUENCE posts_id_seq RESTART WITH 1;")
            self.conn.commit()
            print("Table 'posts' has been reset and ID sequence restarted.")
        except (Exception, psycopg2.Error) as error:
            print(f"Error resetting table: {error}")
            self.conn.rollback()

    def setup_database(self):
        try:
            self.conn = psycopg2.connect(**self.db_params)
            self.cursor = self.conn.cursor()
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS posts (
                    id SERIAL PRIMARY KEY,
                    author TEXT,
                    content TEXT,
                    email TEXT,
                    phone_number TEXT,
                    UNIQUE (author, content)
                )
            ''')
            self.conn.commit()
            print("Database connection established and table created/verified.")
        except (Exception, psycopg2.Error) as error:
            print(f"Error while connecting to PostgreSQL: {error}")
            if self.conn:
                self.conn.close()
            raise

    def click_more_button(self):
        try:
            while True:
                more_buttons = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_all_elements_located((By.XPATH, "//span[text()='…more']"))
                )
                if not more_buttons:
                    logging.info("No '...more' buttons found. Moving on.")
                    break
                
                for button in more_buttons:
                    try:
                        WebDriverWait(self.driver, 10).until(
                            EC.element_to_be_clickable(button)
                        )
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", button)
                        self.driver.execute_script("arguments[0].click();", button)
                        logging.info("Clicked '...more' button")
                    except (StaleElementReferenceException, TimeoutException) as e:
                        logging.warning(f"Could not click '...more' button: {e}")
                        continue
                
                # Wait for any animations or page updates to complete
                time.sleep(2)
            
        except TimeoutException:
            logging.info("No more '...more' buttons found or timeout occurred. Moving on.")
        except Exception as e:
            logging.error(f"Error during clicking '...more' button: {e}")

    def clean_author_name(self, author):
        # Remove any "hashtag" from the author name
        author = re.sub(r'^hashtag\s*', '', author)
        if '\n' in author:
            return author.split('\n')[0].strip()
        return author.strip()

    def clean_content(self, content):
        # Remove redundant hashtags
        content = re.sub(r'hashtag\s*#', '#', content)
        # Remove consecutive newlines
        content = re.sub(r'\n+', '\n', content)
        return content.strip()

    def extract_phone_number(self, content):
        # This regex pattern covers various phone number formats
        phone_pattern = r'\b(?:\+?(\d{1,3}))?[-. (]*(?:\d{3})[-. )]*\d{3}[-. ]*\d{4}\b'
        match = re.search(phone_pattern, content)
        return match.group(0) if match else None

    def post_exists(self, author, content):
        try:
            self.cursor.execute(
                "SELECT COUNT(*) FROM posts WHERE author = %s AND content = %s",
                (author, content)
            )
            count = self.cursor.fetchone()[0]
            return count > 0
        except (Exception, psycopg2.Error) as error:
            print(f"Error checking for existing post: {error}")
            return False

    def search_posts(self):
        try:
            search_bar = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "search-global-typeahead__input"))
            )
            search_bar.send_keys(self.search_query)
            search_bar.send_keys(Keys.RETURN)
            time.sleep(5)

            logging.info("Searching for content tab...")
            filter_section = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "search-reusables__filters-bar"))
            )
            logging.info("Filter section found.")

            filter_options = filter_section.find_elements(By.XPATH, ".//button")

            content_tab = None
            for option in filter_options:
                if 'Posts' in option.text:
                    content_tab = option
                    break

            if content_tab:
                logging.info("Content tab found. Clicking...")
                content_tab.click()
            else:
                logging.info("Content tab not found. Proceeding with default view.")
            
            time.sleep(5)

            logging.info(f"Current URL: {self.driver.current_url}")

        except (TimeoutException, NoSuchElementException) as e:
            logging.error(f"Search failed: {str(e)}")
            self.driver.save_screenshot("search_error.png")
            logging.info("Error screenshot saved as search_error.png")
            self.driver.quit()
            raise

    def login(self):
        self.driver.get("https://www.linkedin.com/login")
        try:
            username_field = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            password_field = self.driver.find_element(By.ID, "password")
            
            username_field.send_keys(self.username)
            password_field.send_keys(self.password)
            password_field.send_keys(Keys.RETURN)

            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.ID, "global-nav"))
            )
            logging.info("Login successful")

        except (TimeoutException, NoSuchElementException) as e:
            logging.error(f"Login failed: {str(e)}")
            self.driver.quit()
            raise

    def scrape_posts(self, num_posts=10):
        posts = []
        scroll_attempts = 0
        max_scroll_attempts = 5

        author_elements = [
            ".//span[contains(@class, 'feed-shared-actor__name')]",
            ".//span[contains(@class, 'update-components-actor__name')]",
            ".//span[contains(@class, 'visually-hidden')]",
            ".//span[contains(@class, 'update-components-actor__title')]"
        ]

        content_elements = [
            ".//div[contains(@class, 'feed-shared-update-v2__description')]",
            ".//div[contains(@class, 'feed-shared-text')]",
            ".//div[contains(@class, 'update-components-text')]",
            ".//div[contains(@class, 'feed-shared-update-v2__content')]"
        ]

        while len(posts) < num_posts and scroll_attempts < max_scroll_attempts:
            self.click_more_button()

            post_elements = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'feed-shared-update-v2') or contains(@class, 'occludable-update')]")
            
            for post in post_elements:
                if len(posts) >= num_posts:
                    break
                
                try:
                    author = None
                    for element in author_elements:
                        try:
                            author = post.find_element(By.XPATH, element).text
                            if author:
                                author = self.clean_author_name(author)
                                break
                        except NoSuchElementException:
                            continue

                    if not author:
                        logging.warning("Could not find author name, skipping post")
                        continue

                    content = None
                    for element in content_elements:
                        try:
                            content = post.find_element(By.XPATH, element).text
                            if content:
                                content = self.clean_content(content)
                                break
                        except NoSuchElementException:
                            continue

                    if not content:
                        logging.warning("Could not find post content, skipping post")
                        continue

                    # Check if post already exists in the database
                    if self.post_exists(author, content):
                        logging.info(f"Post by {author} already exists. Skipping.")
                        continue

                    email = None
                    email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', content)
                    if email_match:
                        email = email_match.group(0)

                    phone_number = self.extract_phone_number(content)
                    
                    # Insert the post into the PostgreSQL database
                    try:
                        self.cursor.execute(
                            "INSERT INTO posts (author, content, email, phone_number) VALUES (%s, %s, %s, %s)",
                            (author, content, email, phone_number)
                        )
                        self.conn.commit()
                        logging.info(f"Successfully scraped and stored new post by {author}")
                        posts.append({
                            "author": author,
                            "content": content,
                            "email": email,
                            "phone_number": phone_number
                        })
                    except psycopg2.IntegrityError:
                        self.conn.rollback()
                        logging.warning(f"Duplicate post detected for {author}. Skipping.")
                    except (Exception, psycopg2.Error) as error:
                        logging.error(f"Error inserting post into database: {error}")
                        self.conn.rollback()
                    
                except Exception as e:
                    logging.error(f"Error scraping post: {str(e)}")
                    continue

            # Scroll down to load more posts
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                scroll_attempts += 1
            else:
                scroll_attempts = 0

        return posts

    def run(self):
        try:
            self.setup_database()
            self.reset_table()
            self.login()
            self.search_posts()
            posts = self.scrape_posts()
            return posts
        except Exception as e:
            logging.error(f"An error occurred during scraping: {str(e)}")
            return []
        finally:
            if self.driver:
                self.driver.quit()

    def close_connection(self):
        if self.conn:
            self.cursor.close()
            self.conn.close()
            logging.info("Database connection closed.")

    def get_post_by_id(self, post_id):
        try:
            self.cursor.execute("SELECT * FROM posts WHERE id = %s", (post_id,))
            post = self.cursor.fetchone()
            if post:
                return {
                    "id": post[0],
                    "author": post[1],
                    "content": post[2],
                    "email": post[3],
                    "phone_number": post[4]
                }
            else:
                return None
        except (Exception, psycopg2.Error) as error:
            logging.error(f"Error retrieving post from database: {error}")
            return None

def query_llama(prompt, post_content):
    url = "http://localhost:11434/api/generate"
    
    data = {
        "model": "llama3.1",
        "prompt": f"Based on the following LinkedIn post, {prompt}\n\nPost content: {post_content}",
        "stream": False
    }
    
    response = requests.post(url, json=data)
    
    if response.status_code == 200:
        result = json.loads(response.text)
        return result['response']
    else:
        return f"Error: Unable to get a response from the Llama model. Status code: {response.status_code}"

def main():
    username = "your_email@example.com"
    password = "your_password"
    search_query = "python developer"
    
    db_params = {
        "database": "linkedin",
        "user": "postgres",
        "password": "postgres",
        "host": "localhost",
        "port": "5432"
    }

    scraper = LinkedInPostScraper(username, password, search_query, db_params)
    posts = scraper.run()

    print(f"Scraped {len(posts)} posts and stored them in the PostgreSQL database.")
    print("Press Enter to continue to querying...")
    input()  # Wait for user to press Enter

    # Query specific posts using Llama
    while True:
        post_id = input("Enter the ID of the post you want to query (or 'q' to quit): ")
        if post_id.lower() == 'q':
            break

        post = scraper.get_post_by_id(post_id)
        if post:
            print(f"Post content: {post['content']}")
            user_query = input("Enter your query about this post: ")
            
            llama_response = query_llama(user_query, post['content'])
            print(f"Llama's response: {llama_response}")
        else:
            print(f"No post found with ID {post_id}")

    scraper.close_connection()

if __name__ == "__main__":
    main()