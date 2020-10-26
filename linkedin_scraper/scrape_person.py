from linkedin_scraper import actions
from selenium import webdriver
import time

email =""
password=""

class Linkedin:

    def __init__(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--start-maximized")
        self.driver = webdriver.Chrome("./chromedriver", chrome_options=options)
        actions.login(self.driver, email, password)
        self.driver.get("https://www.linkedin.com/in/mahesh-k-software-engineer/")
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        self.driver.execute_script("window.scrollTo(0, 0);")

    def skills(self):
        flag = self.driver.find_element_by_xpath(
            '/html/body/div[7]/div[3]/div/div/div/div/div[2]/main/div[2]/div[6]/div/section/ol')
        self.driver.execute_script("arguments[0].scrollIntoView();", flag)
        time.sleep(4)
        self.driver.find_element_by_xpath('//h2[text()="Skills & Endorsements"]')
        skills_lst = []
        total_skills = len(
            self.driver.find_elements_by_xpath("//ol[starts-with(@class,'pv-skill-categories-section')]/li"))
        for skill in range(1, total_skills + 1):
            try:
                skill = self.driver.find_element_by_xpath(
                    f"//ol[starts-with(@class,'pv-skill-categories-section')]/li[{skill}]/div/div[2]/p/span").text
            except:
                skill = self.driver.find_element_by_xpath(
                    f"//ol[starts-with(@class,'pv-skill-categories-section')]/li[{skill}]/div/div[2]/p/a/span").text
            skills_lst.append(skill)
        return skills_lst

# print(Linkedin().skills())
