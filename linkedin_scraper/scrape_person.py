from linkedin_scraper import actions
from selenium import webdriver
import time

email = "XXXXXXXX"
password= "XXXXXX"

class Linkedin:

    def __init__(self):
        options = webdriver.ChromeOptions()
        # options.add_argument("--headless")
        options.add_argument("--start-maximized")
        self.driver = webdriver.Chrome("./chromedriver", chrome_options=options)
        actions.login(self.driver, email, password)
        self.driver.get("https://www.linkedin.com/in/mahesh-k-software-engineer/")
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        print("Scrolled to Bottom")

    def skills(self):
        max_wait = 1
        while max_wait <= 10:
            try:
                self.driver.find_element_by_xpath('//h2[text()="Skills & Endorsements"]')
                print("Skills and Endorsements attached to Dom")
                break
            except Exception as e:
                time.sleep(1)
                max_wait +=1

        skills_lst = []
        total_skills = len(
            self.driver.find_elements_by_xpath("//ol[starts-with(@class,'pv-skill-categories-section')]/li"))
        for skill in range(1, total_skills + 1):
            skill_prefix_xpath = f"//ol[starts-with(@class,'pv-skill-categories-section')]/li[{skill}]/div//p"
            try:
                skill = self.driver.find_element_by_xpath(f"{skill_prefix_xpath}/span").text
                print(f"Skill: {skill}")
            except:
                skill = self.driver.find_element_by_xpath(f"{skill_prefix_xpath}/a/span").text
                print(f"Skill: {skill}")
            skills_lst.append(skill)
        return skills_lst


print(Linkedin().skills())

