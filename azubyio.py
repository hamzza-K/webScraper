import time
import selenium
import traceback
import pandas as pd
from kratzen import Suchen
from bs4 import BeautifulSoup
from typing import List, Tuple
from soupmonad import SoupMonad
from settings import getDriver, openSettings
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from shortcuts import soupify, text_from_html, extractEmails
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC

data = openSettings()
show = not data['azubiyo']['openBrowser']
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
        self.driver = getDriver(hide=show)

    def suchify(self, url):
        r = Suchen().create_session(url)
        return BeautifulSoup(r.text, 'html.parser')

    def drives(self, index=4) -> 'selenium.WebDriver':
      try:
        self.driver.get(Azubiyo.url)
        #Handles the `pop-up` that appears on every new instance of a webdriver.
        WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="cmpwelcomebtnyes"]/a'))).send_keys(Keys.ENTER)
        
        self.driver.maximize_window()
        self.driver.implicitly_wait(15)

        # search XPATH
        # location XPATH
        search = '//*[@id="filterSettingsSearchSubjectSearchBox"]'
        to = '//*[@id="filterSettingsSearchLocationSearchBox"]'
        button = '//*[@id="find-jobs-action-btn"]/div/button'
        self.driver.find_element(By.XPATH, to).send_keys(self.state)
        self.driver.find_element(By.XPATH, search).send_keys(self.keyword)
        time.sleep(3)
        self.driver.find_element(By.XPATH, search).send_keys(self.keyword)
        ActionChains(self.driver).move_by_offset(100, 100).pause(2).click().perform()
        # time.sleep(5)
        self.driver.implicitly_wait(10)
        #Dropdown in the site. 
        option = self.driver.find_element(By.XPATH, '//*[@id="hideElementWhenScrollTopReached"]/div[1]/div/div/div[2]/div/div[2]/select')
        drop = Select(option)
        drop.select_by_index(index)
        time.sleep(3)

        self.driver.find_element(By.XPATH, '/html/body/div[7]/main/div[3]/div/div[3]/div')

        try:
          nav = "/html/body/div[7]/main/div[3]/div/div[3]/div/div/nav"
          self.maxPages = len(self.driver.find_element(By.XPATH, nav).text.split())
        except NoSuchElementException:
          self.maxPages = 1

        posted_jobs_xpath = '/html/body/div[7]/main/div[3]/div/div[2]/h2'
        try:
          self.numJobs = self.driver.find_element(By.XPATH, posted_jobs_xpath).text.split()[0]
        except:
          self.numJobs = 0
        print(f'Posted number of jobs: {self.numJobs}')
        # if '.' in self.numJobs:
        #   self.numJobs = self.numJobs.split('.')[0]
        print('there are a total of %r pages' % self.maxPages)


        # if int(self.numJobs) == 0 and self.override:
        #   print(f"Searching for jobs regardless of the area {self.state}")
        #   return self.driver
        
        # if int(self.numJobs) == 0:
        #   print(f"No suitable jobs found in the given city: {self.state}. Skipping.")
          # return None
        return self.driver
      except:
        print(traceback.format_exc())
        print('cannot open %s' % self.driver.current_url)
        return None

    def _linking(self, page: object) -> 'list':
      """Returns all the links and their respective titles found inside a section."""
      links = []
      for e, elem in enumerate(page.find_elements(By.TAG_NAME, 'section')):
        try:
          title = elem.find_element(By.TAG_NAME, 'h3').text
          link = elem.find_element(By.TAG_NAME, 'a').get_attribute('href')
          print(f'{e+1}) {title} | {link}')
          links.append((title, link))
        except NoSuchElementException:
          print(f'{e+1}) has no title')

      return links 

    def _remainingLinks(self, n: int, page: object) -> 'list':
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
        return None

    def checkJobDescriptionEmail(self, url: str) -> 'str':
      soup = soupify(url)
      text = text_from_html(soup)
      email = extractEmails(text)
      return email

    def getSectionEmail(self, soup: BeautifulSoup, date: str, t: str) -> List[Tuple]:
        sec = SoupMonad(soup)
        monad = sec.find('section', {'class': 'pt-3 px-3'}).\
        findAll('div', {'class': 'col-md-10'})
        emails = []
        if monad.value:
          for e, v in enumerate(monad.value):
            name = v.text.split('\n')[2]
            title = sec.find('h1', {'class': 'az-hyphenate mb-2 px-0 px-xl-5 mx-0 mx-xl-5 text-left text-xl-center'})
            if title.value:
              title = title.unwrap().get_text() 
            else:
              title = t
            print(str(e+1) + ')', name, title)
            text = text_from_html(v)
            email = extractEmails(text)
            if email:
              print(f'found: {email}')
              emails.append((title, name, ';'.join(email), date, self.state))
              # print("="*105)
              # print(emails)
              print("-"*105)
              return emails[0]
            else:
              print(f"No email found for {name}")
        else:
          print(monad.error_status)
        return emails

    def infosec(self, lisht: List[Tuple]) -> 'pd.DataFrame':
      scraped = []
      for title, url in lisht:
        print(f'Going to {title}.')
        print("Checking Info Section.")
        # url, title = lisht[1], lisht[0]
        info_url = url + Azubiyo.infosection
        soup = soupify(info_url)
        date = self.getDate(soup)
        emails = self.getSectionEmail(soup, date, title)
        if emails:
          scraped.append(emails)
          # print(scraped)
          # return pd.DataFrame(emails, columns=['Title', 'Name', 'Email', 'Entry Date', 'State'])
        else:
          print("Couldn't find the jobs in information section. Trying job description.")
          email = self.checkJobDescriptionEmail(url)
          if email:
            print(f'found email: {email}')
            scraped.append((title, 'None', email[0], date, self.state))
            # print(scraped)
            # return pd.DataFrame([(title, 'None', email[0], date, self.state)],
            # columns=['Title', 'Name', 'Email', 'Entry Date', 'State'])
          else:
            print('found nothing..')
      return pd.DataFrame(scraped, columns=['Title', 'Name', 'Email', 'Entry Date', 'State'])

    def processEmails(self, lisht: list) -> 'pd.DataFrame':
      # print(f'going to {lisht[1]}')
      return self.infosec(lisht)
        
        
#====================================================================================
# ------------------------------------ Azubiyo --------------------------------------
#====================================================================================
