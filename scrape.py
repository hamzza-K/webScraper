import os
import sys
import time
import datetime
import schedule
import warnings
import selenium
import pandas as pd
from art import text2art
from azubyio import Azubiyo
from career import CareerHotel
from arbeitsa import searchArbeitsa
from selenium.webdriver.common.by import By
from kratzen import searchHoga, searchStellen
from selenium.webdriver.support.ui import WebDriverWait
from settings import openSettings, getDriver, tearDown, profile
from selenium.webdriver.support import expected_conditions as EC


warnings.filterwarnings("ignore")
print(text2art('Kratzen'))

#===============================================
data = openSettings() #|||||||||||||||||||||||||
#===============================================

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



# ---------------------------------------------




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
    captcha: bool = data['arbeitsa']['LookForCaptcha']
    hoga: dict = data['hoga'] 
    hide: bool = data['chrome']['hide']
    hotecareer_searchsize: int = data['hotelcareer']['searchSize']
    
    hotecareer_searchdict = {'0': 'exact',
                             '1': '20',
                             '2': '50',
                             '3': '100',
                             '4': '150'}

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
            career = CareerHotel(state=state, keyword=keyword, driver=getDriver(), debug=True)
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
              df4 = searchArbeitsa(key, region, Ergebnissseite, days, size, umkreis, arbeitszeit, captcha, debug)
              if df4 is not None:
                df = pd.concat([df, df4])
            except Exception as e:
              print('-----------------------------------------------------------------')
              print("--- Couldn't open the Arbeitsa site ---")
              print('-----------------------------------------------------------------')
              print(e)
              print('Trying again in 30 seconds...')
              time.sleep(30)
              df4 = searchArbeitsa(key, region, Ergebnissseite, days, size, umkreis, arbeitszeit, captcha, debug)
              if df4 is not None:
                df = pd.concat([df, df4])

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
              scraped = azu.processEmails(links, page)
              # for link in links:
              #   print('Finding email for %s' % link[0])
              if scraped is not None:
                df = pd.concat([df, scraped])
                page.quit()


  # =============================================================================
      df = df.sort_values('State', ascending=False)
      if data['unique']:
        df = df.drop_duplicates(subset='Email', keep='first')

      df = df.dropna().reset_index()
  # =============================================================================

      time_now  = datetime.datetime.now().strftime('%m_%d_%Y_%H_%M') 
      if data["fileName"] and data["outputPath"]:
        os.chdir(data["outputPath"])
        # with open('captcha_sites.txt', 'w') as f:
        #   for e, link in enumerate(captcha_sites):
        #     f.write(f'{e+1}) - {link}\n')
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

