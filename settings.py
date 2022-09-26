import sys, json
from pymsgbox import alert
from selenium import webdriver
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
profile = data['chrome']['profile']
data_dir = data['chrome']['data-dir']
hide = data['chrome']['hide']
#-----------------------------------------------------------------------
# Configure the driver
def getDriver():
  chrome_options = webdriver.ChromeOptions()
  if hide:
    chrome_options.add_argument('--headless')
  chrome_options.add_argument('--no-sandbox')
  chrome_options.add_argument('--disable-dev-shm-usage')
  chrome_options.add_argument('log-level=3')
  if data_dir:
    chrome_options.add_argument(f'user-data-dir={data_dir}')
  if profile:
    chrome_options.add_argument(f'profile-directory={profile}')
  else:
    chrome_options.add_argument(f'profile-directory=Default')

  return webdriver.Chrome(data['pathToDriver'],options=chrome_options)
#------------------------------------------------------------------------
def tearDown(driver):
    driver.quit()
