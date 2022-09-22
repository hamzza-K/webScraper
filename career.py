import re
import pandas as pd
from bs4 import BeautifulSoup
from bs4.element import Comment
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC

from kratzen import Suchen
from SeleMonad import SeleMonad
from prettytable import PrettyTable
x = PrettyTable()

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

    
  def drives(self, index=4):
    self.driver.get(CareerHotel.hotel_url)
    WebDriverWait(self.driver, 2).until(EC.element_to_be_clickable((By.ID, 'search-form__what'))).send_keys(f'{self.keyword}')
    WebDriverWait(self.driver, 2).until(EC.element_to_be_clickable((By.ID, 'search-form__where'))).send_keys(f'{self.state}')
    self.driver.implicitly_wait(10)
    ActionChains(self.driver).move_by_offset(100, 100).pause(2).click().perform()

    WebDriverWait(self.driver, 1).until(EC.element_to_be_clickable((By.XPATH, "//*[@id='facet-BEREICH']/li[1]/a"))).click()
    WebDriverWait(self.driver, 2).until(EC.element_to_be_clickable((By.ID, 'search-form__where'))).send_keys(Keys.ENTER)
    self.driver.implicitly_wait(10)
    ActionChains(self.driver).move_by_offset(100, 100).pause(2).click().perform()

    option = self.driver.find_element(By.XPATH, '//*[@id="Searchbox_ycg_page_listing"]/div/div[1]/label[3]/span/select')
    drop = Select(option)
    drop.select_by_index(index)
    
    WebDriverWait(self.driver, 1).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="btnSearch_new"]'))).click()
    self.driver.implicitly_wait(10)
    ActionChains(self.driver).move_by_offset(100, 100).pause(2).click().perform()

    # WebDriverWait(self.driver, 1).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="filterbox"]/div/div/div[1]/ul/li[3]/a'))).click()
    # self.driver.find_element(By.XPATH, '//*[@id="filterbox"]/div/div/div[1]/ul/li[3]/a').click()
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
        WebDriverWait(page, 2).until(EC.element_to_be_clickable((By.CLASS_NAME, 'weiter'))).send_keys(Keys.ENTER)
        if i == 0:
          ActionChains(page).move_by_offset(120, 130).pause(2).click().perform()
        soup = BeautifulSoup(page.page_source, 'html.parser')
        links += self.rightResult(soup)
        print(f"Number of links on the {i + 2} Page: ", len(self.rightResult(soup)))

        if self.debug:
          print("=============================================================")
          print(f"----- End of {i + 2} Page -----")
          print("=============================================================")
      except Exception as e:
        print("Page took too long to load.")
        page.implicitly_wait(30)
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
    '''Main method that scrapes the name/email/entrydate from the post.'''
    scraped = []
    idx = 0
    for link in links:
      try:
        idx += 1
        url = CareerHotel.original_url + link[1]
        if link[0] == "None" or link[0] == None:
          title = f'Ausbildung {url.split("/")[4]}'
        self.driver.get(url)
        monad = SeleMonad(self.driver)    
        print(str(idx) + ')')
        print(f'going to {url}...')
        title = monad.find_element(By.CLASS_NAME, 'ycg_info_line').find_element(By.TAG_NAME, 'h1')
        #---------------------------------------------------------------------------------
        #------------------------------------- Title -----------------------------------
        #---------------------------------------------------------------------------------
        if title.contains_value:
          title = title.unwrap().text
        else:
          title = link[0]
        #---------------------------------------------------------------------------------
        #------------------------------------- EmailSection -----------------------------------
        #---------------------------------------------------------------------------------
        emailSection = monad.find_element(By.CLASS_NAME, 'job_section').find_element(By.ID, 'email')
        # print(f'emailSection: {emailSection.contains_value}')
        if emailSection.contains_value:
          email = emailSection.unwrap().text
        else: 
          print('finding further for the email.')
          soup = self.soupify(self.driver)
          t = text_from_html(soup)
          email = extractEmails(t)
          if email:
            email = ';'.join(email) if len(email) > 1 else email
            print(email)
          else:
            print(f'{title} didn\'t have an email..')
            continue
        #---------------------------------------------------------------------------------
        #------------------------------------- Name -----------------------------------
        #---------------------------------------------------------------------------------
        name = monad.find_element(By.CLASS_NAME, 'contact_name')
        # print(f'name: {name.contains_value}')
        if name.contains_value:
          name = name.unwrap().text.encode('ascii', 'ignore').decode('utf-8')
        else:
          print('finding name from general text.')
          name = self.driver.find_element(By.ID, 'contact_container').text.split('\n')
          print(name)
          if '|' in name[-1]:
            name = name[-1].split('|')[0].strip()
            print(f"general_name: {name}")
          elif 'I' in name[-1]:
            name = name[-1].split('I')[0].strip()
            print(f"general_name: {name}")
          else:
            name = name[2]
        #---------------------------------------------------------------------------------
        #------------------------------------- EntryDate -----------------------------------
        #---------------------------------------------------------------------------------
        entrydate = monad.find_element(By.CLASS_NAME, 'date')
        # print(f'entrydate: {entrydate.contains_value}')
        if entrydate.contains_value:
          entrydate = entrydate.unwrap().text
        else:
          entrydate = None
        if email:
          if self.debug:
            print(f'email found: {title} | {email} | {entrydate} | {name}')
            print('-'*95)
          scraped.append((title, name, email, entrydate, self.state))
        else:
          if self.debug:
            print(f'{title} didn\'t have an email..')
          
      except Exception as e:
        print(e)
        continue
    
    self.tearDown()
    return pd.DataFrame(scraped, columns=['Title', 'Name', 'Email', 'Entry Date', 'State'])