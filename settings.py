import sys, json
from pymsgbox import alert
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities



def openSettings():
    try:
        with open("settings.json", encoding='utf-8-sig') as f:
            data = json.load(f)
            # print('loading settings.json file..')
        return data
    except FileNotFoundError as e:
        alert(text="Settings.json file was not loaded. Please Load the file and try again.", title="Settings File not Found", button="OK")
        sys.exit()

data = openSettings()

caps = DesiredCapabilities.CHROME
caps['goog:loggingPrefs'] = {'performance': 'ALL'}

profile = data['chrome']['profile']
data_dir = data['chrome']['data-dir']
hide = data['chrome']['hide']
#-----------------------------------------------------------------------
# Configure the driver
def getDriver(arbeitsa=False):
  chrome_options = webdriver.ChromeOptions()
  if hide:
    chrome_options.add_argument('--headless')
  chrome_options.add_argument('--no-sandbox')
  chrome_options.add_argument('--disable-dev-shm-usage')
  chrome_options.add_argument('log-level=3')
  chrome_options.add_argument("window-size=1900x1200")
  if arbeitsa and data_dir:
    chrome_options.add_argument(f'user-data-dir={data_dir}')
  if arbeitsa and profile:
    chrome_options.add_argument(f'profile-directory={profile}')
  # else:
  #   chrome_options.add_argument(f'profile-directory=Default')

  return webdriver.Chrome(data['pathToDriver'],options=chrome_options, desired_capabilities=caps)
#------------------------------------------------------------------------
def tearDown(driver):
    driver.quit()
