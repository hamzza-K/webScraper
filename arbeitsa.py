import re
import requests
import pymsgbox
import pandas as pd
from PIL import Image
import urllib.request
from soupmonad import SoupMonad
from selemonad import SeleMonad
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from kratzen import Hoga, Suchen
from prettytable import PrettyTable
from bs4 import BeautifulSoup, Comment
from settings import getDriver, tearDown
from selenium.webdriver.common.by import By
import time, traceback, matplotlib, base64, warnings
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC



x = PrettyTable()
captcha_sites = []
warnings.filterwarnings("ignore")


#--------------------------------------------------------------------------------
#------------------------------------- Arbeitsa ---------------------------------
#--------------------------------------------------------------------------------
def soupify(url):
    driver = getDriver()

    driver.get(url)
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')

    tearDown(driver)    
    return soup

def isContentPresent(soup, debug=False) -> bool:
  soup = SoupMonad(soup)
  jd = soup.find('jb-job-detail-stellenbeschreibung').find('h3')
  if jd.value:
    if jd.value.text == 'Stellenbeschreibung':
      print('post contains job description... Searching for email')
      print(jd.value.text)
      return True
  return False

def isCaptchaPresent(driver: object) -> bool:
  try:
    driver.find_element(By.ID, 'jobdetails-kontaktdaten-heading').text
    return True
  except Exception:
    return False

def isCaptchaSolved(driver: object) -> bool:
  try:
    WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.ID, 'kontaktdaten-captcha-image')))
    return False
  except:
    return True

def isCookiePopUpHidden(driver: object) -> bool:
  driver.implicitly_wait(10)
  attribute = driver.find_element(By.TAG_NAME, 'bahf-cookie-disclaimer-dpl3').get_attribute('aria-hidden')
  return False if attribute == 'false' else True

def byPassCookiePopUp(driver: object) -> 'object':
  script: str = """return document.querySelector('bahf-cookie-disclaimer-dpl3').shadowRoot.querySelector("button[aria-label='Alle zulassen – Alle Cookies werden akzeptiert']")"""
  driver.execute_script(script).click()
  return driver

def getCaptchaPic(url: str) -> 'matplotlib.pyplot':
  # url = driver.find_element(By.ID, 'kontaktdaten-captcha-image').get_attribute('src')
  img = mpimg.imread(url)
  imgplot = plt.imshow(img)
  plt.axis('off')
  plt.show()

def getPic(url: str):
  img = Image.open(requests.get(url, stream=True).raw)
  return img

def solvingCaptcha(solved: str, driver: object) -> 'object':
  driver.find_element(By.ID, 'kontaktdaten-captcha-input').send_keys(solved)
  time.sleep(3)
  try:
    WebDriverWait(driver, 5).\
    until(EC.element_to_be_clickable((By.ID, 'kontaktdaten-captcha-absenden-button'))).click()
    return driver
  except Exception as e:
  # driver.find_element(By.ID, 'kontaktdaten-captcha-absenden-button').click()
    print(e)
    return driver

def getCaptchaDetails(driver: object) -> tuple:
  try:
    details = SeleMonad(driver)
    details = details.find_element(By.ID, 'jobdetails-kontaktdaten')
    email = details.find_element(By.ID, 'jobdetail-angebotskontakt-email')
    email = email.unwrap().text if email.contains_value else None
    name = details.find_element(By.ID, 'jobdetail-angebotskontakt-adresse')
    name = name.unwrap().text.split('\n')[0] if name.contains_value else 'No Name'
    if email:
      return name, email
    return None
  except:
    print(traceback.format_exc())
    return None

def getCaptchaUrl(driver: object) -> str:
  sele = SeleMonad(driver)
  sele = sele.find_element(By.ID, 'kontaktdaten-captcha-image')
  if sele.contains_value:
    return sele.unwrap().get_attribute('src')
  print('Failed to get the captcha URL.')
  return None


#=========================================================================================
def processCaptchaJobs(driver: object, url: str) -> tuple:
  if not isCookiePopUpHidden(driver):
    print('Cookie popup was present. Resolved.')
    driver = byPassCookiePopUp(driver)
  while not isCaptchaSolved(driver):
    print('Captcha was not solved.')
    addr = getCaptchaUrl(driver)
    getPic(addr).show()
    solve_captcha = pymsgbox.prompt('Please enter the captcha values.')
    if solve_captcha:
      print(f'Entering: {solve_captcha}')
      driver = solvingCaptcha(solve_captcha, driver)
    else:
      break
            # logs_raw = driver.get_log("performance")
    if not getCaptchaDetails(driver) and not isCaptchaSolved(driver):
      message = pymsgbox.confirm('You Entered the wrong Captcha. Retry?',
              'Confirm Captcha',
              ['Yes', 'No'])
      if message == 'No':
        print(f'Skipping the post: {url}')
        break
  return getCaptchaDetails(driver)
#=========================================================================================
def suchify(url):
  return Suchen().create_session(url)

def isContentLinkPresent(soup, debug=False) -> bool:
  soup = SoupMonad(soup)
  ext = soup.find('a', {'id': 'jobdetails-externeUrl'})
  if ext.value:
    if debug:
      print('Job post contains external link...')
    return True
  print('post contains no external link.')
  return False

def isExternalLink(soup, debug=True) -> bool:
  soup = SoupMonad(soup)
  ext = soup.find('jb-job-detail-stellenbeschreibung').find('a')
  if ext.value:
    if ext.value.text == ' Externe Seite öffnen':
      print('post shares external link...trying to reach it.')
      return True
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
        return state
    except:
        return None

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

#-------------------------------------------------------------------------------------------------
def searchArbeitsa(key: str, region: str, page: int,
 days: int, size: str, umkreis: int, arbeitszeit: str, captcha: bool, debug: bool, pretty: bool = False):
  print('-------------------------------------------------------------------------------------------')
  print('Searching for jobs in ' + region + ' with keyword ' + key)
  print('-------------------------------------------------------------------------------------------')
  
  scraped = []
  d = getDriver(True)

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
              state = getState(jobDetails)
              state = state if state else region
              title = getTitle(jobDetails)
              name, entry_date = getNameAndEntryDate(jobDetails)
              if True:
                print(f'state: {state} and title: {title}')
                d.get(url)
                html = d.page_source
                soup = BeautifulSoup(html, 'html.parser')
                emails = []
                foundEmail = False
                if captcha and isCaptchaPresent(d):
                  print('Captcha is Present.')
                  val = processCaptchaJobs(d, url)
                  if val:
                    name, email = val
                    print(f'Found email in the captcha description. {email}')
                    print(f'Name: {name}')
                    emails.append(email)
                    foundEmail = True
                    captcha_sites.append(url)
                  else:
                    print('did not find email in the captcha desc.')
                  print('------------------------------------')
                else:
                  print('Captcha is not Present.')
                if not foundEmail and isContentPresent(soup, debug):
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
                      print('Couldn\'t open link: ' + url)

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
                  scraped.append(['Arbeitsa | ' + title, name, ' | '.join(map(str, emails)), entry_date, state])
                else:  
                  print(f'There were no emails found for id {id}. Skipping this job.')  
              # else:
              #   print('Link is not valid')
            except KeyError:
              print(f'state {region} not recognized for this offer. Moving to the next one.')
              patience -= 1
              if patience == 0:
                print('-----------------------------------------------------------------')
                print(f'Run out of patience. State {region} not found. Exiting...')
                print('-----------------------------------------------------------------')
                break
              continue
      except:
        print(traceback.format_exc())
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
#-------------------------------------------------------------------------------------------------