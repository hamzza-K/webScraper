import re
import traceback
import pandas as pd
import requests_html
from bs4 import BeautifulSoup
from soupmonad import SoupMonad
from prettytable import PrettyTable
from requests_html import HTMLSession
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


x = PrettyTable()


wiki = "https://en.wikipedia.org/wiki"
origin_hoga = "https://www.hogapage.de"
origin_stellen = "https://www.ihk-lehrstellenboerse.de/"

pattern = re.compile(r"^(\w+)(,\s*\w+)*$")

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
# ----------------------------------------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------------------------------------
class Hoga:

  def __init__(self, origin: str, source, debug: bool=False):
    self.source = source
    self.origin = origin
    self.debug = debug

  def _findArticles(self) -> list:
    soup = BeautifulSoup(self.source, 'html.parser')
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
      print('returning total of ' + str(len(links)) + ' links')
    return links

  @staticmethod
  def getEmail(link: str) -> str:
    email = None
    newlink = Suchen().create_session(link)
    soup = BeautifulSoup(newlink.text, 'html.parser')
    soup = SoupMonad(soup)
    meta = soup.find('div', {'class':'hp_job-detail-meta'})
    a = meta.findAll('a').unwrap()
    if meta.value:
      name = soup.find('div', {'class':'hp_job-detail-meta'}).\
      find('div', {'class':'position-relative mb-hp_smaller'}).\
      unwrap().\
      get_text(strip=True, separator='\n').splitlines()
      entry_date = soup.find('div', {'class':'hp_job-detail-header'}).\
      find('li', {'class':'icon-clock m-0'}).unwrap().text
      for i in range(len(a)):
        if a[i].get('content'):
          email = a[i].get('content')
          if email:
            print(f'email found!')
            break
      return name, email, entry_date
    return None, None, None

  def findEmail(self, hoga, state=None) -> list:
    emails = []
    links = self._findArticles()

    searchAll = hoga['searchAll']
    limit = hoga['limit']

    if not searchAll:
      links = links[:limit] if limit < len(links) else links
      print('searching only ' + len(links) + ' links')

    # idx = 0
    for e, link in enumerate(links):
      # idx += 1
      l = self.origin + link[1]
      # newlink = Suchen().create_session(l)

      if self.debug:
        print(str(e) + ')')
        print(f'going to {l}')
      # soup = BeautifulSoup(newlink.text, 'html.parser')
      # meta = soup.find('div', {'class':'hp_job-detail-meta'})
      # a = meta.find_all('a')
      # name = soup.find('div', {'class':'hp_job-detail-meta'}).\
      # find('div', {'class':'position-relative mb-hp_smaller'}).\
      # get_text(strip=True, separator='\n').splitlines()
      # entry_date = soup.find('div', {'class':'hp_job-detail-header'}).\
      # find('li', {'class':'icon-clock m-0'}).text
      # for i in range(len(a)):
      #   if a[i].get('content'):
      #     email = a[i].get('content')
      #     if self.debug:
      #       print(f'email found!')
      #     break
      name, email, entry_date = Hoga.getEmail(l)

      if email:
        if state:
          # x.align = 'r'
          # x.field_names = ['name', 'email', 'entry_date', 'state']  
          # try:           
          #   x.add_row([name[1], email, entry_date, state])
          #   print(f'{e}) {name[1]} - {email} - {entry_date} - {state}')
          #   emails.append((link[0], name[1], email, entry_date, state))
          #   if self.debug:
          #     if e > 5:
          #       print(x.get_string(start=e - 5, end=e))
          #     else:
          #       print(x)
          # except IndexError:
          print(f'{name} - {email} - {entry_date}')
          emails.append((link[0], name[1], email, entry_date, state))
        else:
          emails.append((link[0], name[1], email, entry_date, 'None'))
      else:
        print('Found no emails.')

    return emails
# ----------------------------------------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------------------------------------
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

    # if self.debug:
    #   print(data)

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

    idx = 0

    for title in links:
      idx += 1
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
        name = soup.find('div', {'class': 'contentBox clearfix contactBox'}).find_all('p')[-3].text
        beginn = soup.find('table', {'class': 'jobDetailList'}).find_all('td')

        blisht = []
        for b in beginn:
          blisht.append("".join(b.get_text(strip=True, separator='\n').splitlines()))

        indx = blisht.index('Beginn')
        if self.debug:
          x.align = 'r'
          x.field_names = ['title', 'name', 'email', 'entry_date', 'state']
          x.add_row([title[0], name, email, blisht[indx+1], state])
          if idx >= 5:
            print(x.get_string(start=idx-5, end=idx))
          else:
            print(x)
          # print(f'{state} - {name} - {email} - {blisht[indx+1]}')

        emails.append((title[0], email, state))

      except AttributeError as e:
        print(e)
        if self.debug:
          print(f'{title[0]} has no email. Skipping...')
        email = None

    return emails
# ----------------------------------------------------------------------------------------------------------------------
  

# ----------------------------------------------------------------------------------------------------------------------
def searchHoga(keywords, states, hoga, debug, fn):
  h_emails = []
  k = []
  for key in keywords:
    print(f'Searching for keyword: {key}..')
    for state in states:
      print(f'searching for the state: {state}..')
      # hoga_url = f"https://www.hogapage.de/jobs/suche?q={key}&where={state}&radius=200"
      revised_hoga = f"https://www.hogapage.de/jobs/suche?q=Auszubildende+m%2Fw%2Fd+{key}&where={state}&radius=200"
      try:
        source = fn(revised_hoga)
        h = Hoga(origin_hoga, source, debug)
        h_emails.append(h.findEmail(hoga, state=state))
        
        mail = [i for i in h_emails]
        for i in mail:
          for m in i:
            k.append(m)
      except Exception as e:
        print(traceback.format_exc())
        print(f'{key} - {state} - no results')
        continue

  return pd.DataFrame(k, columns=['Title', 'Name', 'Email', 'Entry Date', 'State'])
# ----------------------------------------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------------------------------------
def searchStellen(depth, state, debug):
  k = []
  for i in range(depth):
    stellen_url = f"https://www.ihk-lehrstellenboerse.de/angebote/suche?hitsPerPage=10&page={i}&sortColumn=-1&sortDir=asc&query=9&organisationName=Unternehmen+eingeben&status=1&mode=1&dateTypeSelection=LASTCHANGED_DATE&location={state}&thisYear=true&nextYear=true&afterNextYear=true&distance=0"
    s = Stellen(stellen_url, origin_stellen, debug)
    k.append(s.findEmail())
    
    lisht = [i for m in k for i in m]
    lisht.sort(key = lambda lisht: lisht[-1])

  return pd.DataFrame(lisht, columns=['Title', 'Name', 'Email', 'Entry Date', 'State'])
# ----------------------------------------------------------------------------------------------------------------------
