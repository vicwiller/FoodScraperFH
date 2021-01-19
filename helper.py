from models import *
import requests
import re
from bs4 import BeautifulSoup


def IntersparProduct_exists(id):
    x = db.session.query(
        db.session.query(IntersparProduct).filter_by(id=id).exists()
    ).scalar()
    return x


def get_IntersparSubcategories():
    page = requests.get('https://www.interspar.at/shop/lebensmittel/obst-gemuese/saisonartikel/c/F2-1-1/')
    soup = BeautifulSoup(page.content, 'html.parser')
    urls = soup.find_all('a', {'href': re.compile(r'c\/F\d\d?-\d\d?-\d\d?')})
    list = []
    for url in urls:
        x = url.get("href")
        list.append(x)
    return list

def get_billa_brands():
    page = requests.get('https://www.billa.at/marken')
    soup = BeautifulSoup(page.content, 'html.parser')
    body = soup.find("div", class_="body-content")
    marken = soup.find_all("a", href=True)
    markenliste = []
    for marke in marken:
        x = marke.text.strip()
        markenliste.append(x)
    return markenliste


def get_UnimarktSubcategories():
    page = requests.get('https://shop.unimarkt.at/fleisch-wurst')
    soup = BeautifulSoup(page.content, 'html.parser')
    menu = soup.find("ul", class_="navbar-nav")
    urls = soup.find_all('li')
    list = []
    for url in urls:
        try:
            x = url.a.get("href")
            list.append(x)
        except:
            continue
    #setCategories = set(list)

    # if main category delete. want subthings
    #mainCategories = {'/haushalt', '/milchprodukte', '/brot-gebaeck', '/tiefkuehl', '/obst-gemuese', '/getraenke', '/suesses-snacks', '/lebensmittel', '/fleisch-wurst'}
    #cleaned = setCategories - mainCategories
    #finalList = list(cleaned)
    return list# not necessary. main cats and scrolling



# li.active = currently active menubutton can have subbutton
def isSmallestUnimarktCategory(driver):
    try:
        submenu = driver.find_element_by_css_selector('.subnav li.active ul li.active')
        return False  # if this exists there is a subcategory
    except:
        return True  # there is no sub category


