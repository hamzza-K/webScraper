import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from selenium.webdriver.common.by import By
import selenium, time, traceback, matplotlib
from settings import getDriver
from selemonad import SeleMonad
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image
import requests
import pymsgbox


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
  return None

def processCaptchaJobs(driver: object, url: str) -> tuple:
  driver.get(url)
  present = isCaptchaPresent(driver)
  print('Captcha present for', url, '-', present)
  if present:
    time.sleep(2)
    if not isCookiePopUpHidden(driver):
      print('Cookie pop was present.')
      driver = byPassCookiePopUp(driver)
    while not isCaptchaSolved(driver):
      print('Captcha was not solved.')
      addr = getCaptchaUrl(driver)
      getPic(addr).show()
      solve_captcha = pymsgbox.prompt('Please enter the captcha values.')
      if solve_captcha:
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
        name, email = getCaptchaDetails(driver)
        return name, email
  else:
    print('No captcha found.')
    None

# driver = getDriver(False)
# driver.maximize_window()
# with open('C:\\Users\\hk151\\docs\\captcha_sites.txt', 'r') as f:
#     for e, v in enumerate(f):
#         url = v.strip()[4:]
#         if url.startswith('-'):
#             url = url[2:]
#         url = url.strip()
#         print(f'{e}) - going to {url}')
#         processCaptchaJobs(driver, url)
        # driver.get(url)
        # present = isCaptchaPresent(driver)
        # print('Captcha present for', url, '-', present)
        # if present:
        #   time.sleep(2)
        #   if not isCookiePopUpHidden(driver):
        #     print('Cookie pop was present.')
        #     driver = byPassCookiePopUp(driver)
        #   while not isCaptchaSolved(driver):
        #     print('Captcha was not solved.')
        #     addr = getCaptchaUrl(driver)
        #     getPic(addr).show()
        #     solve_captcha = pymsgbox.prompt('Please enter the captcha values.')
        #     if solve_captcha:
        #       driver = solvingCaptcha(solve_captcha, driver)
        #     else:
        #       break
        #     # logs_raw = driver.get_log("performance")
        #     if not getCaptchaDetails(driver) and not isCaptchaSolved(driver):
        #       message = pymsgbox.confirm('You Entered the wrong Captcha. Retry?',
        #       'Confirm Captcha',
        #       ['Yes', 'No'])
        #       if message == 'No':
        #         print(f'Skipping the post: {url}')
        #         break
        #   print(f'{e}) details for {url} \n', getCaptchaDetails(driver))

        #   print('---------------------------------------------------------------------------')
        # else:
        #   print('No captcha found.')

time.sleep(30)