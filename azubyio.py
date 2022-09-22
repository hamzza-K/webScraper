import sys
import traceback
import re, json, time
import pandas as pd
import urllib.request
from typing import Dict
from bs4 import BeautifulSoup
from bs4.element import Comment
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
from pymsgbox import *
from kratzen import Suchen

postwithemail = 'https://www.azubiyo.de/stellenanzeigen/ausbildung-zum-koch-m-w-d_drv-bayern-sued_gde5bg21/'
url = "https://www.azubiyo.de/ausbildung/hamburg/hotefachmann"
original_url = "https://www.azubiyo.de"
uurl = "https://www.azubiyo.de/ausbildung/"
xpath = "/html/body/div[7]/main/div[3]/div/div[3]/div/div[1]/div"


pattern = re.compile(r'[\w.+-]+@[\w-]+\.[\w.-]+')


def openSettings():
    try:
        with open("settings.json", encoding='utf-8-sig') as f:
            data = json.load(f)

        print('loading settings.json file..')
        return data
    except FileNotFoundError as e:
        alert(text="Settings.json file was not loaded. Please Load the file and try again.", title="Settings File not Found", button="OK")
        sys.exit()

#===============================================
data = openSettings() #|||||||||||||||||||||||||
#===============================================

# ------------------------Selenium Configuration--------------------------------------------
sys.path.insert(0,'/usr/lib/chromium-browser/chromedriver')
from selenium import webdriver
chrome_options = webdriver.ChromeOptions()
if data['chrome']['hide']:
  chrome_options.add_argument('--headless')
chrome_options.add_argument('--log-level=3')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36")
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument("window-size=1920x1080")
# ------------------------Selenium Configuration--------------------------------------------


def getDriver():
  return webdriver.Chrome(data['pathToDriver'],options=chrome_options)

def tearDown(driver):
  driver.quit()

def soupify(url):
  driver = getDriver()
  driver.get(url)
  html = driver.page_source
  soup = BeautifulSoup(html, 'html.parser')
  tearDown(driver)
  return soup

# ------------------------SoupMonad--------------------------------------------
class SoupMonad:
  def __init__(self, value: object = None, error_status: Dict = None):
    self.value = value
    self.error_status = error_status

  def __repr__(self):
    return f"SoupMonad({self.value}, {self.error_status})"

  def unwrap(self):
    return self.value

  def find(self, *args) -> 'SoupMonad':
    if self.error_status:
      return SoupMonad(None, error_status=self.error_status)
    try:
      result = self.value.find(*args,)
      return SoupMonad(result)
    except Exception as e:
      failure_status = {
          'trace': traceback.format_exc(),
          'exc': e,
          'args': args,
      }
      return SoupMonad(None, error_status=failure_status)

  def findAll(self, *args) -> 'SoupMonad':
    if self.error_status:
      return SoupMonad(None, error_status=self.error_status)
    try:
      result = self.value.findAll(*args,)
      return SoupMonad(result)
    except Exception as e:
      failure_status = {
          'trace': traceback.format_exc(),
          'exc': e,
          'args': args,
      }
      return SoupMonad(None, error_status=failure_status)
    
  @staticmethod
  def wrap(value):
    return SoupMonad(value)
# ------------------------SoupMonad--------------------------------------------

def tag_visible(element):
    if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
        return False
    if isinstance(element, Comment):
        return False
    return True

def text_from_html(soup):
    # soup = BeautifulSoup(body, 'html.parser')
    texts = soup.findAll(text=True)
    visible_texts = filter(tag_visible, texts)  
    return u" ".join(t.strip() for t in visible_texts)

def extractEmails(input_string) -> str:
  return re.findall(r'[\w.+-]+@[\w-]+\.[\w.-]+', input_string)


html = urllib.request.urlopen(postwithemail).read()

#====================================================================================
# ------------------------------------ Azubiyo --------------------------------------
#====================================================================================
class Azubiyo:
    url = "https://www.azubiyo.de/ausbildung/"
    stellen = "https://www.azubiyo.de/stellenmarkt/"
    uurl = "https://www.azubiyo.de/ausbildung/berlin/hotelfachmann/"
    postwithemail = 'https://www.azubiyo.de/stellenanzeigen/ausbildung-zum-koch-m-w-d_drv-bayern-sued_gde5bg21/'
    postwithnoemail = 'https://www.azubiyo.de/stellenanzeigen/ausbildung-verkaeuferin-m-w-d-kauffrau-im-einzelha_edeka_8c64e34b/'
    postwithcontact = "https://www.azubiyo.de/stellenanzeigen/ausbildung-zum-handelsfachwirt-m-w-d-brandenburg_deichmann_c42a826d/"
    infosection = "#/ausbilderprofil"

    def __init__(self, state, keyword, override=False, debug=False):
        self.state = state
        self.keyword = keyword
        self.debug = debug
        self.url = Azubiyo.url + self.state + "/" + self.keyword
        self.override = override
        self.maxPages = 0
        self.numJobs = 0
        self.driver = getDriver()

    def suchify(self, url):
        r = Suchen().create_session(url)
        return BeautifulSoup(r.text, 'html.parser')

    def drives(self, index=4):
      try:
        self.driver.get(Azubiyo.url)
        WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="cmpwelcomebtnyes"]/a'))).send_keys(Keys.ENTER)
        
        self.driver.maximize_window()
        self.driver.implicitly_wait(15)

        search = '//*[@id="hideElementWhenScrollTopReached"]/div[1]/div/div/div[1]/div/span/input'
        to = '//*[@id="hideElementWhenScrollTopReached"]/div[1]/div/div/div[2]/div/div[1]/span/input'
        self.driver.find_element(By.XPATH, to).send_keys(self.state)
        # WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.XPATH, to))).send_keys(self.state)
        self.driver.implicitly_wait(15)
        # time.sleep(3)
        self.driver.find_element(By.XPATH, search).send_keys('')
        time.sleep(3)
        self.driver.find_element(By.XPATH, search).send_keys(self.keyword)
        # WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.XPATH, search))).send_keys(self.keyword)
        self.driver.implicitly_wait(15)
        time.sleep(3)
        option = self.driver.find_element(By.XPATH, '//*[@id="hideElementWhenScrollTopReached"]/div[1]/div/div/div[2]/div/div[2]/select')
        drop = Select(option)
        drop.select_by_index(index)

        self.driver.find_element(By.XPATH, '/html/body/div[7]/main/div[3]/div/div[3]/div')

        try:
          nav = "/html/body/div[7]/main/div[3]/div/div[3]/div/div/nav"
          self.maxPages = len(self.driver.find_element(By.XPATH, nav).text.split())
        except NoSuchElementException:
          self.maxPages = 1

        self.numJobs = self.driver.find_element(By.XPATH, '/html/body/div[7]/main/div[3]/div/div[2]/h2').text.split()[0]
        print('Posted number of jobs: %r' % self.numJobs)
        print('there are a total of %r pages' % self.maxPages)


        if int(self.numJobs) == 0 and self.override:
          print(f"Searching for jobs regardless of the area {self.state}")
          return self.driver
        
        if int(self.numJobs) == 0:
          print(f"No suitable jobs found in the given city: {self.state}. Skipping.")
          return None
        return self.driver
      except Exception as e:
        print('cannot open %s' % self.driver.current_url)
        return None

    def _linking(self, page):
      """Returns all the links and their respective titles found inside a section."""
      links = []
      for e, elem in enumerate(page.find_elements(By.TAG_NAME, 'section')):
        try:
          title = elem.find_element(By.TAG_NAME, 'h3').text.strip(' ') 
          link = elem.find_element(By.TAG_NAME, 'a').get_attribute('href')
          print('%r) %s | %s' % (e+1, title, link))
          links.append((title, link))
        except NoSuchElementException:
          print(f'{e+1}) has no title')

      return links 

    def _remainingLinks(self, n, page) -> 'list':
      links = []
      for i in range(n - 1):
        try:
          print("=============================================================")
          print(f"----- On {i + 2} Page -----")
          print("=============================================================")

          curr_url = Azubiyo.stellen + f'{i + 2}'
          page.get(curr_url)
          page.implicitly_wait(10)
          l = self._linking(page)
          links += l
          print(f"Number of links on the {i + 2} Page: ", len(l))

          print("=============================================================")
          print(f"----- End of {i + 2} Page -----")
          print("=============================================================")
        except Exception:
          print("Page took too long to load.")
          continue

      page.quit()
      return links

    def getAllLinks(self, page):
      first = self._linking(page)

      if self.maxPages > 1:
        remaining = self._remainingLinks(self.maxPages, page)
        total = first + remaining
        print(f"Returning total of: {len(total)} links.")
        return total
      print(f"Returning total of: {len(first)} links.")
      page.quit()
      return first

    def getDate(self, soup) -> str:
        monad = SoupMonad(soup)
        monad = monad.find('div', {'id': 'showCompanyInfo'}).\
        find('ul', {'class': 'list-unstyled info-box'}).\
        find('span', {'class': 'ml-2 az-hyphenate'})
        if monad.value:
            return monad.unwrap().text
        else:
            return monad.error_status

    def checkJobDescriptionEmail(self, url: str):
      soup = soupify(url)
      text = text_from_html(soup)
      email = extractEmails(text)
      return email

    def getSectionEmail(self, soup, date, t: str):
        monad = SoupMonad(soup)
        monad = monad.find('section', {'class': 'pt-3 px-3'}).\
        findAll('div', {'class': 'col-md-10'})
        emails = []
        if monad.value:
          for e, v in enumerate(monad.value):
            title = v.text.split('\n')[2]
            print(str(e+1) + ')', title)
            text = text_from_html(v)
            email = extractEmails(text)
            if email:
              print(f'found: {email}')
              emails.append((t, title, email[0], date, self.state))
              print("="*105)
              print(emails)
              print("="*105)
            else:
              print(f"No email found for {title}")
        else:
          return monad.error_status
        return emails

    def infosec(self, lisht):
      print("Checking Info Section.")
      url, title = lisht[1], lisht[0]
      info_url = url + Azubiyo.infosection
      soup = soupify(info_url)
      date = self.getDate(soup)
      emails = self.getSectionEmail(soup, date, title)
      if emails:
        return pd.DataFrame(emails, columns=['Title', 'Name', 'Email', 'Entry Date', 'State'])
      else:
        print("Couldn't find the jobs in information section. Trying job description.")
        email = self.checkJobDescriptionEmail(url)
        if email:
          print(f'found email: {email}')
          return pd.DataFrame([(title, 'None', email[0], date, self.state)],
          columns=['Title', 'Name', 'Email', 'Entry Date', 'State'])
        else:
          print('found nothing..')
          return None

    def processEmails(self, lisht):
        print(f'going to {lisht[1]}')
        return self.infosec(lisht)
        
        
#====================================================================================
# ------------------------------------ Azubiyo --------------------------------------
#====================================================================================


if __name__ == "__main__":


  keywords = data['keywords']
  cities = data['azubiyo']['cities']
  azyubio_area = data['azubiyo']['searchSize']
  for key in keywords:
    for city in cities:
      print(f'searching for keyword: {key} and city: {city} in the area: {azyubio_area}km')
      azu = Azubiyo(city, key, override=False, debug=True)
      page = azu.drives(azyubio_area)
      if page:
        links = azu.getAllLinks(page)
        print('posted jobs: ', azu.numJobs, type(azu.numJobs))
        print('returning total links:', len(links))
        if int(azu.numJobs) < len(links):
          links = links[:int(azu.numJobs)]
        print(f'searching for total {len(links)} links.')
        for link in links:
          print('Finding email for %s' % link[0])
          print(azu.processEmails(link))
        page.quit()

