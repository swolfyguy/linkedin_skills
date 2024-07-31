import logging
import os
import time
from unicodedata import category

from selenium import webdriver
from selenium.webdriver import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement


class CATEGORY:
    PEOPLE = "People"


class initializer:
    def __init__(self, username, password, query, personalized_note=None):
        # chrome_options = webdriver.ChromeOptions()
        # chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
        # chrome_options.add_argument("--headless")
        # chrome_options.add_argument("--disable-dev-shm-usage")
        # chrome_options.add_argument("--no-sandbox")
        self.driver = webdriver.Chrome()
        # self.driver = webdriver.Chrome("src/resources/chromedriver")
        self.driver.maximize_window()
        self.username = username
        self.password = password
        self.query = query
        f"""
        I noticed that you are a recruiter. I’m a Software Engineer with 7+ years Experience and currently seeking new opportunities. 
        I’d love to find out if I may be a fit for any of your current openings, 
        and I’d also be happy to conn1ect you with other professionals in my field
        """
        if not personalized_note:
            self.personalized_note = f"""
I noticed that you are a recruiter. I’m a Software Engineer with 8+ years Experience. 
I’d love to connect with you for future opportunities and I am more than happy to help you connect with my network and I am sure that it will be beneficial for both of us
"""
        else:
            self.personalized_note = personalized_note

    def open_linkedin(self):
        self.driver.get("https://www.linkedin.com/")

    def quit_browser(self):
        self.driver.quit()

    def login(self):
        self.click_element(self.get_element(by=By.LINK_TEXT, value="Sign in"))
        self.enter_text(
            self.get_element(by=By.ID, value="username"), value=self.username
        )
        self.enter_text(
            self.get_element(by=By.ID, value="password"), value=self.password
        )
        self.get_element(by=By.XPATH, value="//button[@type='submit']").submit()

    def search_query(self):
        time.sleep(2)
        search_ele = self.get_element(
            by=By.XPATH,
            value="//input[@placeholder='Search for jobs, skills, companies...']",
        )
        if not search_ele:
            # Sometime instead of 'Search for jobs, skills, companies...' its only 'Search'
            search_ele = self.get_element(
                by=By.XPATH, value="//input[@placeholder='Search']"
            )

        search_ele.click()
        search_ele.send_keys(self.query)
        search_ele.send_keys(Keys.ENTER)

    def click_query_category(self, category):
        categories_ele = self.get_elements(by=By.XPATH, value="//div[@id='search-reusables__filters-bar']/ul")
        for category_index in range(1, len(categories_ele) + 1):
            category_ele = self.get_element(by=By.XPATH,
                                            value=f"//div[@id='search-reusables__filters-bar']/ul/li[{category_index}]/button")
            if category_ele.text == "People":
                category_ele.click()
                break

        # category_ele = self.get_element(
        #     by=By.XPATH, value="//div[@id='search-reusables__filters-bar']/ul/li[1]/button", time_=20
        # )
        # category_ele.click()

    def connect_people(self):
        def refresh_connect_eles(connect_eles):
            for _ in range(10):
                try:
                    connect_eles[1].get_attribute("class");
                    return connect_eles
                except:
                    connect_eles = self.get_elements(
                        by=By.XPATH, value="//span[text()='Connect']", time_=20
                    )
                    time.sleep(1)

        count = 1
        while True:
            time.sleep(5)
            class_ = "entity-result__actions entity-result__divider"
            connect_eles = self.get_elements(
                by=By.XPATH, value="//span[text()='Connect']", time_=20
            )
            connect_parent_ele_xpath = f"div[@class='{class_}']/button"
            # for index in range(1, 11):
            #     follow_or_invite_str = self.get_element(
            #         by=By.XPATH,
            #         value=f"//ul[@class='reusable-search__entity-result-list list-style-none']/li[{index}]//{connect_parent_ele_xpath}/span",
            #     ).text
            if connect_eles:
                loop = len(connect_eles)
                for index in range(loop) or []:
                    # close any opened messaging dialogue
                    message_dialogues_ele = self.get_elements(by=By.XPATH, value="//aside[@id='msg-overlay']/div")
                    if len(message_dialogues_ele) != 3:
                        for _index in range(2, len(message_dialogues_ele) - 1):
                            self.click_element(by=By.XPATH,
                                               value=f"//aside[@id='msg-overlay']/div[{_index}]//li-icon[@type='close']")
                            time.sleep(1)

                    connect_ele = connect_eles[index]
                    recruiter_name = connect_ele.find_element(by=By.XPATH, value="..").get_attribute(
                        "aria-label"
                    )[7:][:-11]

                    print("recruiter name: ", recruiter_name)

                    recruiter_personalized_note = (
                        f"Hi {recruiter_name}, {self.personalized_note}"
                    )

                    # connect_ele = refresh_connect_eles(connect_eles)[index]
                    # Click Connect
                    time.sleep(2)
                    connect_ele.click()
                    time.sleep(2)
                    # self.click_element(
                    #     self.get_element(
                    #         by=By.XPATH, value=f"{connect_parent_ele_xpath}/span"
                    #     )
                    # )
                    # Click Add a Note

                    send_connect_header_ele = self.get_element(by=By.XPATH, value="//h2[@id='send-invite-modal']")
                    if "How do you know" in send_connect_header_ele.text:
                        self.click_element(by=By.XPATH, value="//button[@aria-label='Other']")
                        time.sleep(1)
                        self.click_element(by=By.XPATH, value="//button[@aria-label='Connect']")
                        time.sleep(1)

                    send_ele = self.get_element(
                        by=By.XPATH, value="//span[text()='Send without a note']"
                    )
                    send_ele.click()
                    # if send_ele.is_enabled():
                    #
                    #     self.click_element(
                    #         by=By.XPATH, value="//button[@aria-label='Add a note']"
                    #     )
                    #     # Enter personalized Note
                    #     self.enter_text(
                    #         self.get_element(by=By.ID, value="custom-message"),
                    #         value=recruiter_personalized_note,
                    #     )
                    #     # Click Send Now
                    #     self.click_element(send_ele)
                    #     print(f"sent connection to {recruiter_name}")
                    #
                    #     print("sleep", end=" ")
                    #     _sleep = 1
                    #     while _sleep < 10:
                    #         try:
                    #             self.driver.find_element(by=By.CLASS_NAME, value='artdeco-toast-item__content')
                    #             self.get_elements(by=By.XPATH,
                    #                               value="//div[@data-test-artdeco-toast-item-type='error']/button")[
                    #                 0].click()
                    #             time.sleep(1)
                    #             break
                    #         except:
                    #             time.sleep(1)
                    #             print(_sleep, end=" ")
                    #             _sleep += 1
                    #     else:
                    #         print("total requests sent: ", count)
                    #         count = count + 1
                    #     print()
                    # else:
                    #     self.click_element(
                    #         by=By.XPATH,
                    #         value="//div[@role='dialog']/button[@aria-label='Dismiss']",
                    #     )
                    #     time.sleep(1)

            self.driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);"
            )
            time.sleep(2)
            next_page_ele = self.get_element(by=By.XPATH, value="//span[text()='Next']")
            self.driver.execute_script("arguments[0].scrollIntoView();", next_page_ele)
            # click next page
            self.click_element(next_page_ele)

    def get_element(self, by: By, value: str, time_: int = 10):
        counter = 1
        while counter < time_:
            try:
                return self.driver.find_element(by=by, value=value)
            except Exception as e:
                time.sleep(1)
                counter += 1

    def get_elements(self, by: By, value: str, time_: int = 10):
        for _ in range(1, time_):
            if eles := self.driver.find_elements(by=by, value=value):
                return eles
            time.sleep(1)

    def click_element(
            self,
            element: WebElement = None,
            by: By = None,
            value: str = None,
            time_: int = 10,
    ):
        counter = 1
        while counter < time_:
            try:
                if element:
                    element.click()
                else:
                    self.get_element(by=by, value=value).click()
                break
            except Exception as e:
                time.sleep(1)
                counter += 1

    @staticmethod
    def enter_text(element: WebElement, value: str, time_: int = 10):
        counter = 1
        while counter < time_:
            try:
                element.send_keys(value)
                break
            except Exception as e:
                time.sleep(1)
                counter += 1


def main(i, param0, param1):
    try:

        if i == 0:
            args = param0
        else:
            args = param1
        driver = initializer(**args)
        driver.open_linkedin()
        driver.login()
        driver.search_query()
        driver.click_query_category(category=CATEGORY.PEOPLE)
        driver.connect_people()
        driver.quit_browser()
    except Exception as e:
        # main(i, param0, param1)
        logging.info(e)
        raise e

if __name__ == "__main__":
    print("running on heroku....")
    param0 = {
        "username": "email_is",
        "password": "password",
        "query": "hiring python developer",
        "personalized_note": f"""
        """
    }
    param1 = {
    }

    main(0, param0, param1)
