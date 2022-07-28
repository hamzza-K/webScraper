import sys, re, warnings, json, requests, base64, time, schedule, datetime, os
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
from bs4.element import Comment
import urllib.request
from art import text2art
import pandas as pd
from pymsgbox import *

from kratzen import searchHoga, searchStellen, Suchen

warnings.filterwarnings("ignore")

wiki = "https://en.wikipedia.org/wiki"

pattern = re.compile(r"^(\w+)(,\s*\w+)*$")

print(text2art('Kratzen'))

def openSettings():
    try:
        with open("settings.json", "r") as f:
            data = json.load(f)

        print('loading settings.json file..')
        return data
    except FileNotFoundError as e:
        alert(text="Settings.json file was not loaded. Please Load the file and try again.", title="Settings File not Found", button="OK")
        sys.exit()

#===============================================
data = openSettings() #|||||||||||||||||||||||||
#===============================================
#-----------------------------------------------------------------------
# Configure the driver
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('log-level=3')
#------------------------------------------------------------------------
driver = webdriver.Chrome(data['pathToDriver'],options=chrome_options)


# ------------------------------ CAREER HOTEL --------------------------------
class CareerHotel:
  original_url = "https://www.hotelcareer.de"
  hotel_url = "https://www.hotelcareer.de/jobs/ausbildung"


  def __init__(self, debug):
    self.debug = debug
  
  def suchify(self, url):
    r = Suchen().create_session(url)

    return BeautifulSoup(r.text, 'html.parser')

  def getLinks(self, soup, debug: bool=False) -> list:
    links = soup.find('body').find('ul', {'id': 'resultlist'}).find_all('li')

    lisht = []

    for link in links:
      title = link.find('h2').text
      reference = link.find('a').get('href')
      location = link.find('span', {'class': 'mb-2'}).text
      if not location:
        location = 'None'
      if debug:
        print(f'title is : {title} and link: {reference} and location: {location}')
      lisht.append((title, reference, location))
    return lisht

  def getEmail(self, soup):
    soup.find('body').find('div', {'class', 'job_section'}).find('a').text


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
    


  def processScrape(self, url):


    driver.get(url)
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    links = self.getLinks(soup)
    scraped = []

    for link in links:
      url = CareerHotel.original_url + link[1]

      state = self.handlerState(link[2])

      if state == "None":
        state = link[2]      

      soup = self.suchify(url)
      if self.debug:
        print(f'going to {url}...')
      emailSection = soup.find('body').find('div', {'class', 'job_section'}).find('a')

      if emailSection:
        email = emailSection.text
      else:
        email = None

      if email:
        if self.debug:
          print(f'email found: {email}')
        scraped.append((link[0], email, state))
      else:
        if self.debug:
          print(f'{url.split("/")[4]} didn\'t have an email..')
      
    return pd.DataFrame(scraped, columns=['Title', 'Email', 'State'])
# ------------------------------ CAREER HOTEL --------------------------------




def soupify(url):
    driver.get(url)
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    return soup

def isContentPresent(soup, debug=False) -> bool:
  try:
    jd = soup.find('jb-job-detail-stellenbeschreibung').find('h3')

    if jd == None:
      raise AssertionError
    assert jd.text == 'Stellenbeschreibung'
    if debug:
      print('post contains job description... Searching for email')
    return True
  except AssertionError:
    if debug:
      print('post contains no job description. Moving forward..')
    return False

def isContentLinkPresent(soup, debug=False) -> bool:
  try:
    link = soup.find('a', {'id': 'jobdetails-externeUrl'})
    if link == None:
      raise AssertionError
    if debug and link:
      print('Job post contains external link..searching for email')
    return True
  except (AttributeError, AssertionError) as e:
    if debug:
      print('post contains no external link..')
    return False

def isExternalLink(soup, debug=False) -> bool:
  try:
    ext = soup.find('jb-job-detail-stellenbeschreibung').find('a')

    if ext == None:
      raise AssertionError
    assert ext.text == ' Externe Seite öffnen'
    if debug:
      print('post contains external link..')
    return True
  except AssertionError:
    if debug:
      print('post contains no external link.')
    return False

def getContentLink(soup) -> str:
  return soup.find('a', {'id': 'jobdetails-externeUrl'}).text

def getExternalLink(soup) -> str:
  return soup.find('jb-job-detail-stellenbeschreibung').find('a').get('href')

def getHtml(link, debug=False):
    try:
        html = urllib.request.urlopen(link).read()
        return html
    except urllib.error.HTTPError:
        return None

def tag_visible(element):
    if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
        return False
    if isinstance(element, Comment):
        return False
    return True

def text_from_html(body):
    soup = BeautifulSoup(body, 'html.parser')
    texts = soup.findAll(text=True)
    visible_texts = filter(tag_visible, texts)  
    return u" ".join(t.strip() for t in visible_texts)

def extractEmails(input_string) -> str:
  return re.findall(r'[\w.+-]+@[\w-]+\.[\w.-]+', input_string)

def get_jwt():
    """fetch the jwt token object"""
    headers = {
        'User-Agent': 'Jobsuche/2.9.2 (de.arbeitsagentur.jobboerse; build:1077; iOS 15.1.0) Alamofire/5.4.4',
        'Host': 'rest.arbeitsagentur.de',
        'Connection': 'keep-alive',
        'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8',
    }

    data = {
      'client_id': 'c003a37f-024f-462a-b36d-b001be4cd24a',
      'client_secret': '32a39620-32b3-4307-9aa1-511e3d7f48a8',
      'grant_type': 'client_credentials'
    }

    response = requests.post('https://rest.arbeitsagentur.de/oauth/gettoken_cc', headers=headers, data=data, verify=False)

    return response.json()

def search(jwt, what, where, searchSize=10):
    """search for jobs. returns a list of job references"""
    params = (
        ('angebotsart', '1'),
        ('page', '1'),
        ('pav', 'false'),
        ('size', searchSize),
        ('umkreis', '200'),
        ('was', what),
        ('wo', where),
    )

    headers = {
        'User-Agent': 'Jobsuche/2.9.2 (de.arbeitsagentur.jobboerse; build:1077; iOS 15.1.0) Alamofire/5.4.4',
        'Host': 'rest.arbeitsagentur.de',
        'OAuthAccessToken': jwt,
        'Connection': 'keep-alive',
    }

    response = requests.get('https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v4/app/jobs',
                            headers=headers, params=params, verify=False)
    return response.json()

def job_details(jwt, job_ref):

    headers = {
        'User-Agent': 'Jobsuche/2.9.3 (de.arbeitsagentur.jobboerse; build:1078; iOS 15.1.0) Alamofire/5.4.4',
        'Host': 'rest.arbeitsagentur.de',
        'OAuthAccessToken': jwt,
        'Connection': 'keep-alive',
    }

    response = requests.get(
        f'https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v2/jobdetails/{(base64.b64encode(job_ref.encode())).decode("UTF-8")}',
        headers=headers, verify=False)

    return response.json()

def getStateAndTitle(details: dict) -> tuple:
    """returns the state and title of the job"""
    try:
        state = details['arbeitgeberAdresse']['region']
        title = details['titel']
    except KeyError:
        state = None
        title = None

    finally:
        return state, title

# ----------------------------------------------------------------------------------------------------------------------
def searchArbeitsa(key, region, size, debug):
  print('-----------------------------------------------------------------')
  print('Searching for jobs in ' + region + ' with keyword ' + key)
  print('-----------------------------------------------------------------')
  result = search(jwt["access_token"], key, region, size)          
  
  scraped = []
  try:
    for i in range(len(result['stellenangebote'][::-1])):
      id = result['stellenangebote'][i]["refnr"]
      url = "https://www.arbeitsagentur.de/jobsuche/jobdetail/" + id
      print('going to url: ' + url)
      jobDetails = job_details(jwt["access_token"], id)
      print(f"Release date: {jobDetails['ersteVeroeffentlichungsdatum']}")
      state, title = getStateAndTitle(jobDetails)        
      if state != None and title != None:
        print(f'state: {state} and title: {title}')
        soup = soupify(url)
        emails = []
        foundEmail = False
        #making the driver wait
        driver.implicitly_wait(10)
        if isContentPresent(soup, debug):
          text = soup.find('jb-job-detail-stellenbeschreibung').find('p').get_text(strip=True, separator='\n').splitlines()
          for i in text[::-1]:
            e = extractEmails(i)
            if e:
              print(f'found email: {e}')
              foundEmail = True
              emails.append(e)

        elif isContentPresent(soup) and isContentLinkPresent(soup, debug) and not foundEmail:
          link = getContentLink(soup)
          print(f'going to {link}...')
          html = getHtml(link)
          if html:
            t = text_from_html(html)
            e = extractEmails(t)
            if e:
              print(f'found email! {e}')
              emails.append(e)
              foundEmail = True
            else:
              print('found no email.')
          else:
            print('Couldn\'t open link: ' + link)
        elif isExternalLink(soup, debug) and not foundEmail:
          link = getExternalLink(soup)
          print(f'going to {link}...')
          html = getHtml(link)
          if html:
            t = text_from_html(html)
            e = extractEmails(t)
            if e:
              print(f'found email! {e}')

              emails.append(e)
            else:
              print('found no email.')
          else:
            print('Couldn\'t open link: ' + link)
        if emails:
          scraped.append([title, emails[0][0], state])
        else:  
          print(f'There were no emails found for id {id}. Skipping this job.')  
      else:
        print('Link is not valid')
  except KeyError:
    print(f'state {region} not recognized.')

    
  return pd.DataFrame(scraped, columns=['Title', 'Email', 'State']) if scraped else None
  # return scraped
# ----------------------------------------------------------------------------------------------------------------------




if __name__ == '__main__':

    keywords = data['keywords'] # list of keywords
    regions = data['states'] # list of states
    debug = data['debug'] # if true, the scraper will print out logs
    depth = data['depth'] # how many pages to scrape
    size = data['searchSize'] # number of jobs to search for each keyword
    t = data['scheduler']['interval'] # how often to scrape


    jwt = get_jwt()
    start_time = time.time()


    def job():
      df = pd.DataFrame(columns=['Title', 'Email', 'State'])

      if data["searchHoga"]:
        print('-----------------------------------------------------------------')
        print("--- Searching HogaPage site ---")
        print('-----------------------------------------------------------------')

        df1 = searchHoga(keywords, regions, debug)
        df = pd.concat([df, df1])
      if data["searchStellen"]:
        print('-----------------------------------------------------------------')
        print("--- Searching Stellen site ---")
        print('-----------------------------------------------------------------')

        df2 = searchStellen(depth, debug)
        df = pd.concat([df, df2])
      if data["searchCareer"]:
        print('-----------------------------------------------------------------')
        print("--- Searching CareerHotel site ---")
        print('-----------------------------------------------------------------')

        scraper = CareerHotel(debug)
        df3 = scraper.processScrape(scraper.hotel_url)
        df = pd.concat([df, df3])
      if data['searchArbeitsa']:
        for key in keywords:
          for region in regions:
            df4 = searchArbeitsa(key, region, size, debug)
            if df4 is not None:
              df = pd.concat([df, df4])





  # =============================================================================
      # df = pd.concat([df1, df2, df3])
      df = df.sort_values('State', ascending=False)
      if data['unique']:
        df = df.drop_duplicates(subset='Email', keep='first')
      df = df.dropna().reset_index()
  # =============================================================================

      time_now  = datetime.datetime.now().strftime('%m_%d_%Y_%H_%M') 
      if data["fileName"] and data["outputPath"]:
        os.chdir(data["outputPath"])
        print('-----------------------------------------------------------------')
        print(f"--- File saved to location {data['outputPath']} as {data['fileName']} ---")
        print('-----------------------------------------------------------------')
        df.to_excel(time_now + data["fileName"], index=False)

      elif data["fileName"] and not data["outputPath"]:
        print('-----------------------------------------------------------------')
        print(f"--- File saved to location {os.getcwd()} as {data['fileName']} ---")
        print('-----------------------------------------------------------------')
        df.to_excel(time_now + data["fileName"], index=False)
      else:
        df.to_excel(f'{time_now}output.xlsx', index=False)
      

    if data['searchEveryHour']:
      print(f'Scheduling job to run every {t} hour.')
      schedule.every(t).hours.do(job)
    elif data['searchEveryMinute']:
      print(f'scheduling job to run every {t} minute.')
      schedule.every(t).minutes.do(job)
    elif data['searchEveryDay']:
      print(f'scheduling job to run every {t} day.')
      schedule.every(t).day.do(job)
    elif data['searchEveryWeek']:
      print(f'scheduling job to run every {t} week.')
      schedule.every(t).week.do(job)
    else:
      job()

    if data['scheduler']['enabled']:
      print('scheduler enabled')
      while True:

        schedule.run_pending()
        time.sleep(1)
    else:
      print('scheduler disabled')
      job()
    print('-----------------------------------------------------------------')
    print("--- %s seconds ---" % (time.time() - start_time))
    print('-----------------------------------------------------------------')
    print("Done! Press any key to exit.")
    input()
    sys.exit()

