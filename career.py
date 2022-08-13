import sys, re, warnings, json, requests, base64, time, schedule, datetime, os

import selenium
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

from bs4 import BeautifulSoup
from bs4.element import Comment

from kratzen import Suchen

import pandas as pd


import selenium
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

from selenium.webdriver.common.action_chains import ActionChains

from selenium.webdriver.chrome.service import Service

from prettytable import PrettyTable
x = PrettyTable()

s = Service("C:\\webdriver\\chromedriver.exe")



chrome_options = webdriver.ChromeOptions()
# chrome_options.add_argument("start-maximized")
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')


def getDriver() -> selenium.webdriver:
  return webdriver.Chrome(service=s, options=chrome_options)


def tag_visible(element):
    if element.parent.name in ['style', 'script', 'head', 'meta', '[document]']:
        return False
    if isinstance(element, Comment):
        return False
    return True

def text_from_html(soup):
    texts = soup.findAll(text=True)
    visible_texts = filter(tag_visible, texts)  
    return u" ".join(t.strip() for t in visible_texts)

def extractEmails(input_string) -> str:
  return re.findall(r'[\w.+-]+@[\w-]+\.[\w.-]+', input_string)

# ------------------------------ CAREER HOTEL --------------------------------
class CareerHotel:
  original_url = "https://www.hotelcareer.de"
  hotel_url = "https://www.hotelcareer.de/jobs/ausbildung"


  def __init__(self, state, keyword, driver, debug: bool=True):
    self.debug = debug
    self.state = state
    self.keyword = keyword
    self.driver = driver
    self.maxPages = 0

  def suchify(self, url):
    r = Suchen().create_session(url)
    return BeautifulSoup(r.text, 'html.parser')

  def soupify(self, obj):
    return BeautifulSoup(obj.page_source, 'html.parser')


  def extractEmails(self, input_string) -> str:
    return re.findall(r'[\w.+-]+@[\w-]+\.[\w.-]+', input_string)

    
  def drives(self):
    self.driver.get(CareerHotel.hotel_url)
    WebDriverWait(self.driver, 2).until(EC.element_to_be_clickable((By.ID, 'search-form__what'))).send_keys(f'Ausbildung {self.keyword}')
    WebDriverWait(self.driver, 2).until(EC.element_to_be_clickable((By.ID, 'search-form__where'))).send_keys(f'{self.state}')
    self.driver.implicitly_wait(10)
    ActionChains(self.driver).move_by_offset(100, 100).pause(2).click().perform()

    WebDriverWait(self.driver, 1).until(EC.element_to_be_clickable((By.XPATH, "//*[@id='facet-BEREICH']/li[1]/a"))).click()
    WebDriverWait(self.driver, 2).until(EC.element_to_be_clickable((By.ID, 'search-form__where'))).send_keys(Keys.ENTER)
    self.driver.implicitly_wait(10)
    ActionChains(self.driver).move_by_offset(100, 100).pause(2).click().perform()

    self.maxPages = int(self.driver.find_element(By.CLASS_NAME, 'maxPage').text.split(' ')[-1])

    return self.driver


  def remainingPages(self, n, page):
    links = []
    for i in range(n - 1):
      try:
        if self.debug:
          print("=============================================================")
          print(f"----- On {i + 2} Page -----")
          print("=============================================================")

        # self.driver.implicitly_wait(10)
        # time.sleep(2)
        WebDriverWait(page, 2).until(EC.element_to_be_clickable((By.CLASS_NAME, 'weiter'))).send_keys(Keys.ENTER)
        # page.implicitly_wait(10)
        # ActionChains(page).move_by_offset(100, 100).pause(2).click().perform()
        # time.sleep(3)
        soup = BeautifulSoup(page.page_source, 'html.parser')
        links += self.rightResult(soup)
        print(f"Number of links on the {i + 2} Page: ", len(self.rightResult(soup)))

        if self.debug:
          # print(links, end='\n')
          print("=============================================================")
          print(f"----- End of {i + 2} Page -----")
          print("=============================================================")
      except Exception as e:
        print("Page took too long to load.")
        continue

    return links


  def rightResult(self, soup):
    right = soup.find_all('div', {'class': 'result_list_right'})

    links = []
    for r in right:
      title = r.find('strong')
      link = r.find('a').get('href')
      if self.debug:
        print(f"Found title: {title} and link: {link}")
      links.append((title.text if title else "None", link))
    return links


  def getAllLinks(self, soup, page=None):
    firstpage = self.rightResult(soup)

    print("Number of links on first page: ", len(firstpage))
    
    print(f"There are total: {self.maxPages} pages.")
    if self.maxPages > 1:
      remaining = self.remainingPages(self.maxPages, page)

      total = firstpage + remaining
      print(f"Returning total of: {len(total)} links.")
      return total
    print("Returning total of: ", len(firstpage))
    return firstpage


  def tearDown(self):
    self.driver.quit()




  def processScrape(self, links):
    scraped = []
    idx = 0
    for link in links:
      try:
        idx += 1
        url = CareerHotel.original_url + link[1]
        title = link[0]
        if link[0] == "None" or link[0] == None:
          title = f'Ausbildung {url.split("/")[4]}'    
        soup = self.suchify(url)
        print(str(idx) + ')')
        print(f'going to {url}...')
        emailSection = soup.find('body').find('div', {'class', 'job_section'}).find('a')
        name = soup.find('body').find('div', {'class', 'job_section'}).find('span', {'class': 'contact_name'})
        name = name.text if name else "None"
        entrydate = soup.find('body').find('div', {'class', 'meta_info_container'}).find('span', {'class', 'date'})
        entrydate = entrydate.text if entrydate else "None"
        if emailSection:
          email = emailSection.text
        else:
          if self.debug:
              print(f'Couldn\'t find email. Searching further...')
          # d = getDriver()
          # d.get(url)
          t = text_from_html(soup)
          email = extractEmails(t)
          # d.quit()
          if len(email) > 1:
            # join multiple emails into one string
            print("Found multiple emails.")
            email = ';'.join(email)
            # email = email[0]
          elif len(email) == 1:
            email = email[0]
          else:
              email = None
        if email:
          if self.debug:
            print(f'email: {email} entry: {entrydate} name: {name}')

            # x.align = 'r'
            # x.field_names = ['Title', 'Name', 'Email', 'Entry Date', 'State']
            # x.add_row([title, name, email, entrydate, self.state])
            # print(x.get_string(start=idx, end=idx))
            # if idx > 5:
            #   print(x.get_string(start=idx - 5, end=idx))
            # else:
            #   print(x)
          scraped.append((title, name, email, entrydate, self.state))
        else:
          if self.debug:
            print(f'{url.split("/")[4]} didn\'t have an email..')
      except Exception as e:
        print(e)
        continue
    
    self.tearDown()
      
    return pd.DataFrame(scraped, columns=['Title', 'Name', 'Email', 'Entry Date', 'State'])
# ------------------------------ CAREER HOTEL --------------------------------
# states = ["baden-württemberg"]
# keywords =  ["Hotelfachmann/frau"]
# df = pd.DataFrame(columns=['Title', 'Email', 'State'])
# if __name__ == "__main__":
#   for keyword in keywords:
#     for state in states:
#       print("=============================================================")
#       print(f"----- On {state} with {keyword} -----")
#       print("=============================================================")
#       career = CareerHotel(state=state, keyword=keyword, driver=getDriver(), debug=True)
#       page = career.drives()
#       soup = career.soupify(page)
#       links = career.getAllLinks(soup, page)
#       scraped = career.processScrape(links)
#       if scraped is not None:
#         df = pd.concat([df, scraped])

#     # scraped = scraped.drop_duplicates(subset='Email', keep='first')
#     print((df))

#     print('-----------------------------------------------------------------')
#     print(f"--- File saved to location {os.getcwd()} ---")
#     print('-----------------------------------------------------------------')
#     time_now  = datetime.datetime.now().strftime('%m_%d_%Y_%H_%M') 
#     df.to_excel(f'{time_now}output.xlsx', index=False)