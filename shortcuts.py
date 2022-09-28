import re
from bs4 import BeautifulSoup
from bs4.element import Comment
from settings import getDriver, tearDown

def soupify(url, driver=None):
    if driver:
        driver.get(url)
    else:
        driver = getDriver()
        driver.get(url)
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    tearDown(driver)
    return soup



  



def _tag_visible(element):
    if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
        return False
    if isinstance(element, Comment):
        return False
    return True

def text_from_html(soup):
    # soup = BeautifulSoup(body, 'html.parser')
    texts = soup.findAll(text=True)
    visible_texts = filter(_tag_visible, texts)  
    return u" ".join(t.strip() for t in visible_texts)

def extractEmails(input_string: str) -> list:
    return re.findall(r'[\w.+-]+@[\w-]+\.[\w.-]+', input_string)