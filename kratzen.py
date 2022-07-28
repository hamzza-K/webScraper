import requests, time
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import requests_html
from requests_html import HTMLSession
import re
import pandas as pd



wiki = "https://en.wikipedia.org/wiki"
origin_hoga = "https://www.hogapage.de"
origin_stellen = "https://www.ihk-lehrstellenboerse.de/"

pattern = re.compile(r"^(\w+)(,\s*\w+)*$")

# def openSettings():
#     try:
#         with open("settings.json", "r") as f:
#             data = json.load(f)

#         print('loading settings.json file..')
#         return data
#     except FileNotFoundError as e:
#         alert(text="Settings.json file was not loaded. Please Load the file and try again.", title="Settings File not Found", button="OK")

# #===============================================
# data = openSettings() #|||||||||||||||||||||||||
# #===============================================
# depth = data["depth"]
# keywords = data["keywords"]
# states = data["states"]
# debug = data["debug"]

# ----------------------------------------------------------------------------------------------------------------------
class Suchen:

  def create_session(self, url: str) -> requests_html.HTMLSession:
    """
    Returns a html session 
    Arguments: url (string)
    Returns: HTMLSession
    """
    session = HTMLSession()
    retry = Retry(connect=3, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)

    return session.get(url)


class Hoga:

  def __init__(self, url: str, origin: str, debug: bool=False):
    self.url = url
    self.origin = origin
    self.debug = debug

  def _findArticles(self) -> list:
    r = Suchen().create_session(self.url)
    soup = BeautifulSoup(r.text, 'html.parser')
    articles = soup.find_all('article')

    links = []

    for article in articles:
      try:
        title = article.find('a').text
        link = article.get('data-url')
        if self.debug:
          print(f'found title of article: {title}\
           and the content: {link}')
      except AttributeError:
        if self.debug:
          print(f'article: {article.text[:15]} has no title')
          print('skipping...')
        continue
      links.append((title, link))

    if self.debug:
      print(links)
    return links


  def findEmail(self, state=None) -> list:
    emails = []
    links = self._findArticles()

    for link in links:
      l = self.origin + link[1]
      newlink = Suchen().create_session(l)

      if self.debug:
        print(f'going to {l}')
      soup = BeautifulSoup(newlink.text, 'html.parser')
      meta = soup.find('div', {'class':'hp_job-detail-meta'})
      email = meta.find('a').get('content')

      if email is None:
        if self.debug:
          print('did not find email..Searching further')
        a = meta.find_all('a')

        for i in range(len(a)):
          if a[i].get('content'):
            email = a[i].get('content')
            if self.debug:
              print(f'email found!')
            break

      if self.debug:
        print(f'found {email}')

      if state:
        emails.append((link[0], email, state))
      else:
        emails.append((link[0], email))

    return emails


class Stellen:
  
  def __init__(self, url: str, origin: str, debug: bool=False):
    self.url = url
    self.origin = origin
    self.debug = debug

  def _findTables(self) -> list:
    
    data = []
    r = Suchen().create_session(self.url)
    soup = BeautifulSoup(r.text, 'html.parser')
    table = soup.find('table', {'class': 'sortableTable'})

    rows = table.find('tbody').find_all('tr')

    for row in rows:
      cols = row.find_all('td')
      href = cols[0].find('a').get('href')
      cols = [ele.text.strip() for ele in cols]
      data.append([ele for ele in cols if ele] + [href]) 

    if self.debug:
      print(data)

    return data

  def parse_string(self, input_string) -> str:
    if pattern.match(input_string) == None:
        return (re.sub('\s+', '_', input_string.strip()), 0)
    return (input_string.split(','), 1)

  def getState(self, url) -> str:
    r = Suchen().create_session(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    table = soup.find('table', {'class': 'infobox ib-settlement vcard'})
    try:
      s = table.find('tbody')\
      .find('tr', {'class': 'mergedrow'})\
      .find('td').text
    except AttributeError:
      if self.debug:
        print('didn\'t find the state..')
      s = "None"
    
    return s

  def handlerState(self, raw_str):
    k = self.parse_string(raw_str)
    if k[1] == 1:
      for i in k[0]:
        if self.debug:
          print(f'trying {i}..')
        url = wiki + '/' + i
        r = self.getState(url)
        if r != "None" or i == k[0][-1]:
          if self.debug:
            print(f'state of {i} is {r}')
          return r
          break
      
    else:
      url = wiki + '/' + k[0]
      return self.getState(url)
    


  def findEmail(self) -> list:
    emails = []
    links = self._findTables()

    for title in links:

      l = self.origin + title[-1]
      state = self.handlerState(title[1])
      if state == "None":
        state = title[1]
      newlink = Suchen().create_session(l)

      if self.debug:
        print(f'going to {l}')
      soup = BeautifulSoup(newlink.text, 'html.parser')
      try:
        email = soup.find('p', {'class': 'email'}).text[8:]

        if self.debug:
          print(f'found state for {title[1]}: {state}')
          print(f'found email for {title[0]} : {email}.')

        emails.append((title[0], email, state))

      except AttributeError:
        if self.debug:
          print(f'{title[0]} has no email. Skipping...')
        email = None

    return emails

  

# ----------------------------------------------------------------------------------------------------------------------
def searchHoga(keywords, states, debug):
  h_emails = []
  for key in keywords:
    print(f'Searching for keyword: {key}..')
    for state in states:
      print(f'searching for the state: {state}..')
      hoga_url = f"https://www.hogapage.de/jobs/suche?q={key}&where={state}&radius=200"
      h = Hoga(hoga_url, origin_hoga, debug)
      h_emails.append(h.findEmail(state=state))
      
      mail = [i for i in h_emails]
      k = []
      for i in mail:
        for m in i:
          k.append(m)

  return pd.DataFrame(k, columns=['Title', 'Email', 'State'])
# ----------------------------------------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------------------------------------
def searchStellen(depth, debug):
  k = []
  for i in range(depth):
    stellen_url = f"https://www.ihk-lehrstellenboerse.de/angebote/suche?hitsPerPage=10&page={i}&sortColumn=-1&sortDir=asc&query=9&organisationName=Unternehmen+eingeben&status=1&mode=1&dateTypeSelection=LASTCHANGED_DATE&thisYear=true&nextYear=true&afterNextYear=true&distance=0"
    s = Stellen(stellen_url, origin_stellen, debug)
    k.append(s.findEmail())
    
    lisht = [i for m in k for i in m]
    lisht.sort(key = lambda lisht: lisht[-1])

  return pd.DataFrame(lisht, columns=['Title', 'Email', 'State'])
# ----------------------------------------------------------------------------------------------------------------------
