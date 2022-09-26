import sys, re, warnings, json, requests, base64, time, schedule, datetime, os, traceback

import selenium
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from bs4 import BeautifulSoup
from bs4.element import Comment
import urllib.request
from art import text2art
import pandas as pd
from pymsgbox import *
from prettytable import PrettyTable
from selemonad import SeleMonad

from kratzen import searchHoga, searchStellen, Suchen, Hoga
from career import CareerHotel
from azubyio import Azubiyo
from settings import openSettings, getDriver, tearDown, profile

x = PrettyTable()

warnings.filterwarnings("ignore")
wiki = "https://en.wikipedia.org/wiki"
pattern = re.compile(r"^(\w+)(,\s*\w+)*$")
print(text2art('Kratzen'))

# def openSettings():
#     try:
#         with open("settings.json", encoding='utf-8-sig') as f:
#             data = json.load(f)
#         print('loading settings.json file..')
#         return data
#     except FileNotFoundError as e:
#         alert(text="Settings.json file was not loaded. Please Load the file and try again.", title="Settings File not Found", button="OK")
#         sys.exit()

#===============================================
data = openSettings() #|||||||||||||||||||||||||
#===============================================
# profile = data['chrome']['profile']
# data_dir = data['chrome']['data-dir']
#-----------------------------------------------------------------------
# Configure the driver
# def getDriver(hide: bool = True):
#   chrome_options = webdriver.ChromeOptions()
#   if hide:
#     chrome_options.add_argument('--headless')
#   chrome_options.add_argument('--no-sandbox')
#   chrome_options.add_argument('--disable-dev-shm-usage')
#   chrome_options.add_argument('log-level=3')
#   if data_dir:
#     chrome_options.add_argument(f'user-data-dir={data_dir}')
#   if profile:
#     chrome_options.add_argument(f'profile-directory={profile}')
#   else:
#     chrome_options.add_argument(f'profile-directory=Default')

#   return webdriver.Chrome(data['pathToDriver'],options=chrome_options)
#------------------------------------------------------------------------
# driver = webdriver.Chrome(data['pathToDriver'],options=chrome_options)

# def getDriver():
#   return webdriver.Chrome(data['pathToDriver'],options=chrome_options)

# def tearDown(driver):
#     driver.quit()


def soupify(url):
    driver = getDriver()

    driver.get(url)
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')

    tearDown(driver)    
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


def suchify(url):
  return Suchen().create_session(url)

def isContentLinkPresent(soup, debug=False) -> bool:
  try:
    link = soup.find('a', {'id': 'jobdetails-externeUrl'})
    if link == None:
      raise AssertionError
    if debug and link:
      print('Job post contains external link...')
    return True
  except (AttributeError, AssertionError) as e:
    if debug:
      print('post contains no external link.')
    return False

def isExternalLink(soup, debug=True) -> bool:
  try:

    ext = soup.find('jb-job-detail-stellenbeschreibung').find('a')

    if ext == None:
      raise AssertionError
    assert ext.text == ' Externe Seite öffnen'
    if debug:
      print('post shares external link...trying to reach it.')
    return True
  except AssertionError:
    if debug:
      print('post contains no shared external link.')
    return False

def getContentLink(soup) -> str:
  return soup.find('a', {'id': 'jobdetails-externeUrl'}).text

def getExternalLink(soup) -> str:
  return soup.find('jb-job-detail-stellenbeschreibung').find('a').get('href')

def getHtml(link, debug=True):
  try:
    html = urllib.request.urlopen(link).read()
    return html
  except:
    if debug:
      print(traceback.format_exc())
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

def search(jwt, what, where, page=1, days=7, umkreis=200, arbeitszeit='vz;tz;snw;ho;mj', searchSize=10):
    """search for jobs. returns a list of job references"""
    params = (
        ('angebotsart', '4'),
        ('page', page),
        ('pav', 'false'),
        ('size', searchSize),
        ('umkreis', umkreis),
        ('veroeffentlichtseit', days),
        ('was', what),
        ('wo', where),
        ('arbeitszeit', arbeitszeit)
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

def getState(details: dict) -> str:
    """returns the state of the job"""
    try:
        state = details['arbeitgeberAdresse']['region']
    except KeyError:
        state = "None"
    finally:
        return state

def getTitle(details: dict) -> str:
  """returns the state of the job"""
  try:
    title = details['titel']
  except KeyError:
    title = "None"
  finally:
    return title

def getNameAndEntryDate(details: dict) -> tuple:
    """returns the name and entry date of the job"""
    try:
        name = details['arbeitgeber']
        entry_date = details['eintrittsdatum']
    except KeyError:
        name = None
        entry_date = None
    finally:
        return name, entry_date

def isCaptchaPresent(driver: webdriver) -> bool:
  try:
    driver.find_element(By.ID, 'jobdetails-kontaktdaten-heading').text
    return True
  except Exception:
    return False

def isCaptchaSolved(driver: webdriver) -> bool:
  sele = SeleMonad(driver)
  sele = sele.find_element(By.ID, 'kontaktdaten-captcha-image')
  return sele.contains_value

def getCaptchaDetails(driver: webdriver) -> tuple:
  try:
    # driver.find_element(By.XPATH, '//*[@id="bahf-cookie-disclaimer-modal"]/div/div/div[3]/button[2]/bahf-i18n').click()
    email = driver.find_element(By.ID, 'jobdetails-kontaktdaten').find_element(By.ID, 'jobdetail-angebotskontakt-email').text
    name = driver.find_element(By.ID, 'jobdetail-angebotskontakt-adresse').text
    return name, email  
  except:
    print(traceback.format_exc())
    return None, None

# ----------------------------------------------------------------------------------------------------------------------
def searchArbeitsa(key: str, region: str, page: object,
 days: int, size: str, umkreis: int, arbeitszeit: str, debug: bool, pretty: bool = False):
  print('-------------------------------------------------------------------------------------------')
  print('Searching for jobs in ' + region + ' with keyword ' + key)
  print('-------------------------------------------------------------------------------------------')
  
  scraped = []
  d = getDriver(False)

  try:
    for i in range(page):
      try:
        jwt = get_jwt()
        result = search(jwt["access_token"], key, region, i+1, days, umkreis, arbeitszeit, size)          
        print('-------------------------------------------------------------------------------------------')
        print('Searching page ' + str(i+1) + ' for jobs which were posted in the last ' + str(days) + ' days' + ' and are within ' + str(umkreis) + ' km of ' + region)
        print("Total number of jobs: " + str(len(result['stellenangebote'][::-1])))
        print('-------------------------------------------------------------------------------------------')


        patience = 3
        idx = 0
        if True:
          for i in range(len(result['stellenangebote'][::-1])):
            idx += 1
            try:
              print(f'{i + 1}' + ')')
              id = result['stellenangebote'][i]["refnr"]
              url = "https://www.arbeitsagentur.de/jobsuche/jobdetail/" + id
              print('going to url: ' + url)
              jobDetails = job_details(jwt["access_token"], id)
              print(f"Release date: {jobDetails['ersteVeroeffentlichungsdatum']}")
              # time.sleep(1)
              state = getState(jobDetails)
              state = state if state != "None" else region
              title = getTitle(jobDetails)
              name, entry_date = getNameAndEntryDate(jobDetails)       
              # if state != None and title != None:
              if True:
                print(f'state: {state} and title: {title}')
                d.get(url)
                html = d.page_source
                soup = BeautifulSoup(html, 'html.parser')
                emails = []
                foundEmail = False
                if isCaptchaPresent(d):
                  print('Captcha is Present.')
                  solved = isCaptchaSolved(d)
                  print(f'Captcha Solved: {solved}')
                  # print('Details:', getCaptchaDetails(d))
                  print('------------------------------------')
                else:
                  print('Captcha is not Present.')
                if isContentPresent(soup, debug):
                  text = soup.find('jb-job-detail-stellenbeschreibung').find('p').get_text(strip=True, separator='\n').splitlines()
                  for i in text[::-1]:
                    e = extractEmails(i)
                    if e:
                      print(f'found email inside the post: {e}')
                      print('-----------------------------------------------------------------')
                      foundEmail = True
                      emails.append(e)
                  if not foundEmail:
                    print('no email found inside the post...')

                if not foundEmail and isContentLinkPresent(soup, debug):
                  link = getContentLink(soup)
                  print(f'going to {link}...')
                  if link.split('/')[2] == 'www.hogapage.de':
                    name, e, _ = Hoga.getEmail(link)
                    name = name[1]
                    if e:
                      print(f'found email in the shared link! {e}')
                      print('-----------------------------------------------------------------')
                      emails.append(e)
                      foundEmail = True
                  else:
                    html = getHtml(link)
                    if html:
                      t = text_from_html(html)
                      e = extractEmails(t)
                    if e:
                      print(f'found email in the shared link! {e}')
                      print('-----------------------------------------------------------------')
                      emails.append(e)
                      foundEmail = True
                else:
                  print('found no email in the shared link.')
                  # else:
                  #   print('Couldn\'t open the link: ' + link)
                if not foundEmail and isExternalLink(soup, debug):
                  link = getExternalLink(soup)
                  print(f'going to {link}...')
                  if link.split('/')[2] == 'www.hogapage.de':
                    name, e, _ = Hoga.getEmail(link)
                    name = name[1]
                    if e:
                      print(f'found email in the shared link! {e}')
                      print('-----------------------------------------------------------------')
                      emails.append(e)
                      foundEmail = True
                  else:
                    html = getHtml(link)
                    if html:
                      t = text_from_html(html)
                      e = extractEmails(t)
                      if e:
                        print(f'found email in the external link! {e}')
                        print('-----------------------------------------------------------------')
                        emails.append(e)
                      else:
                        print('found no email in the external link.')
                else:
                  print('Couldn\'t open link: ' + link)

                if emails:
                  print(f'name: {name} and entry date: {entry_date} and state: {state} and title: {"Arbeitsa | " + title} and emails: {emails}')
                  print('-----------------------------------------------------------------')
                  if pretty:
                    x.align = 'r'
                    x.field_names = ['Title', 'Name', 'Email', 'Entry Date', 'State']
                    x.add_row([title, name, emails, entry_date, state])
                    if idx > 5:
                      print(x.get_string(start=idx-5, end=idx))
                    else:
                      print(x)
                  #Get the title using Selenium driver if not found from the API.
                  if title == "None":
                    t = SeleMonad(d)
                    t = t.find_element(By.ID, 'jobdetails-titel')
                    if t.contains_value:
                      title = t.unwrap().text
                  scraped.append(['Arbeitsa | ' + title, name, emails[0][0], entry_date, state])
                else:  
                  print(f'There were no emails found for id {id}. Skipping this job.')  
              else:
                print('Link is not valid')
            except KeyError:
              print(f'state {region} not recognized for this offer. Moving to the next one.')
              patience -= 1
              if patience == 0:
                print('-----------------------------------------------------------------')
                print(f'Run out of patience. State {region} not found. Exiting...')
                print('-----------------------------------------------------------------')
                break
              continue
      except Exception as e:
        print(e)
        # print(traceback.format_exc())
        print('-----------------------------------------------------------------')
        print(f'Couldn\'t get the jwt token for page.')
        print('-----------------------------------------------------------------')
        continue

  except Exception as e:
      print(e)
      print('-----------------------------------------------------------------')
      print(f'Couldn\'t get the jwt token for page. Exiting...')
      print('-----------------------------------------------------------------')
  d.quit()
  return pd.DataFrame(scraped, columns=['Title', 'Name', 'Email', 'Entry Date', 'State']) if scraped else None
  # return scraped


def bypass(url):
  
  driver = getDriver()
  driver.get(url)
  try:
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, 'cmpbntyestxt'))).click()
  except:
    if profile:
      print('profile loaded.')
      pass
    else:
      raise Exception
  
  while 1:
    try:
      WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, 'hp_search-list-load-more'))).click() 
    except Exception as e:
      # print(e)
      print("reached at the end.")
      break
    
  source = driver.page_source
  tearDown(driver)
    
  return source
# ----------------------------------------------------------------------------------------------------------------------




if __name__ == '__main__':

    keywords = data['keywords'] # list of keywords
    regions = data['states'] # list of states
    debug = data['debug'] # if true, the scraper will print out logs
    depth = data['depth'] # how many pages to scrape
    t = data['scheduler']['interval'] # how often to scrape
    days = data['arbeitsa']['days'] # how many days since the job was offered
    Ergebnissseite = data['arbeitsa']['page'] # which page to scrape
    size = data['arbeitsa']['searchSize'] # number of jobs to search for each keyword
    umkreis = data['arbeitsa']['umkreis'] # radius of the search in km
    arbeitszeit = data['arbeitsa']['arbeitszeit']
    hoga = data['hoga'] 
    hide = data['chrome']['hide']
    hotecareer_searchsize = data['hotelcareer']['searchSize']
    
    hotecareer_searchdict = {'0': 'exact',
                             '1': '20',
                             '2': '50',
                             '3': '100',
                             '4': '150'}
    
    jwt = get_jwt()
    start_time = time.time()


    def job():
      df = pd.DataFrame(columns=['Title', 'Name', 'Email', 'Entry Date', 'State'])


      if data["searchCareer"]:
        print('-----------------------------------------------------------------')
        print("--- Searching CareerHotel site ---")
        print('-----------------------------------------------------------------')
        for keyword in keywords:
          for state in regions:
            # print("=============================================================")
            # print(f"----- On {state} with {keyword} -----")
            print(f'searching for keyword: {keyword} and state: {state} in the area: {hotecareer_searchdict[str(hotecareer_searchsize)]}km')
            # print("=============================================================")
            career = CareerHotel(state=state, keyword=keyword, driver=getDriver(hide=hide), debug=True)
            try:
              page = career.drives(hotecareer_searchsize)
              soup = career.soupify(page)
              links = career.getAllLinks(soup, page)
              scraped = career.processScrape(links)
              if scraped is not None:
                df = pd.concat([df, scraped])
            except Exception as e:
              print('-----------------------------------------------------------------')
              print("--- Couldn't open the CareerHotel site ---")
              print('-----------------------------------------------------------------')
              print(e)
              print('Try in another run.')
              pass

      if data["searchHoga"]:
        print('-----------------------------------------------------------------')
        print("--- Searching HogaPage site ---")
        print('-----------------------------------------------------------------')
        try:
          df1 = searchHoga(keywords, regions, hoga, debug, bypass)
          if df1 is not None:
            df = pd.concat([df, df1])
        except (Exception, selenium.common.exceptions.ElementNotInteractableException):
          print('-----------------------------------------------------------------')
          print("--- Couldn't open the HogaPage site ---")
          print('-----------------------------------------------------------------')
          print('Trying again...')
          df1 = searchHoga(keywords, regions, hoga, debug, bypass)
          if df1 is not None:
            df = pd.concat([df, df1])

        except Exception:
          print('-----------------------------------------------------------------')
          print("--- Couldn't open the HogaPage site ---")
          print('-----------------------------------------------------------------')
          print('Trying again in 30 seconds...')
          time.sleep(30)
          df1 = searchHoga(keywords, regions, hoga, debug, bypass)
          if df1 is not None:
            df = pd.concat([df, df1])
        
        except Exception:
          print('-----------------------------------------------------------------')
          print("--- Couldn't open the HogaPage site ---")
          print('-----------------------------------------------------------------')
          print('Try in another run.')
          pass 

      if data['searchArbeitsa']:
        print('-----------------------------------------------------------------')
        print("--- Searching Arbeitsa site ---")
        print('-----------------------------------------------------------------')
        for key in keywords:
          for region in regions:
            try:
              df4 = searchArbeitsa(key, region, Ergebnissseite, days, size, umkreis, arbeitszeit, debug)
              if df4 is not None:
                df = pd.concat([df, df4])
            except Exception as e:
              print('-----------------------------------------------------------------')
              print("--- Couldn't open the Arbeitsa site ---")
              print('-----------------------------------------------------------------')
              print(e)
              print('Trying again in 30 seconds...')
              time.sleep(30)
              df4 = searchArbeitsa(key, region, Ergebnissseite, days, size, umkreis, arbeitszeit, debug)
              if df4 is not None:
                df = pd.concat([df, df4])

            except Exception:
              print('-----------------------------------------------------------------')
              print("--- Couldn't open the Arbeitsa site ---")
              print('-----------------------------------------------------------------')
              print('Try in another run.')
              pass

      if data["searchStellen"]:
              
        print('-----------------------------------------------------------------')
        print("--- Searching Stellen site ---")
        print('-----------------------------------------------------------------')
        for region in regions:
          try:
            df2 = searchStellen(depth, region, debug)
          
            if df2 is not None:
              df = pd.concat([df, df2])
          except Exception:
            print('-----------------------------------------------------------------')
            print("--- Couldn't open the Stellen site ---")
            print('-----------------------------------------------------------------')
            print('Try in another run.')
      
      if data['searchAzubiyo']:
        print('-----------------------------------------------------------------')
        print("--- Searching Azubiyo site ---")
        print('-----------------------------------------------------------------')
        cities = data['azubiyo']['cities']
        override = data['azubiyo']['override']
        azyubio_area = data['azubiyo']['searchSize']

        searchdict = {'0': '10',
                      '1': '25',
                      '2': '50',
                      '3': '100',
                      '4': '250'}
        
        for key in keywords:
          for city in cities:
            print(f'searching for keyword: {key} and city: {city} in the area: {searchdict[str(azyubio_area)]}km')
            azu = Azubiyo(city, key, override=override, debug=True)
            page = azu.drives(azyubio_area)
            if page:
              links = azu.getAllLinks(page)
              print('posted jobs: ', azu.numJobs)
              print('returning total links:', len(links))
              if 0 < int(azu.numJobs) < len(links):
                links = links[:int(azu.numJobs)]
              print(f'searching for total {len(links)} links.')
              for link in links:
                print('Finding email for %s' % link[0])
                scraped = azu.processEmails(link)
                if scraped is not None:
                  df = pd.concat([df, scraped])
                  page.quit()


    # scraped = scraped.drop_duplicates(subset='Email', keep='first')
    # print((df))
    #     scraper = CareerHotel(debug)
    #     df3 = scraper.processScrape(scraper.hotel_url)
    #     df = pd.concat([df, df3])







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

      print('-----------------------------------------------------------------')
      print("--- %s seconds ---" % (time.time() - start_time))
      print('-----------------------------------------------------------------')
      

    if data['searchEveryHour']:
      print(f'Scheduling job to run every {t} hour.')
      job()
      schedule.every(t).hours.do(job)
    elif data['searchEveryMinute']:
      print(f'scheduling job to run every {t} minute.')
      schedule.every(t).minutes.do(job)
    elif data['searchEveryDay']:
      print(f'scheduling job to run every {t} day.')
      job()
      schedule.every(t).day.do(job)
    elif data['searchEveryWeek']:
      print(f'scheduling job to run every {t} week.')
      job()
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

    print("Done! Press any key to exit.")
    input()
    sys.exit()

