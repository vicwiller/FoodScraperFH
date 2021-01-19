import random

from selenium import webdriver
import pandas as pd
from bs4 import BeautifulSoup
import requests
import datetime
import csv
from models import *
import re
import time
import math

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

date = datetime.datetime.now().strftime("%Y-%m-%d")

def handle_cookie_notification(driver):
    try:
        cookie_button = driver.find_element_by_class_name("cookie-notification__button")
        cookie_button.click()
    except:
        return print("Messages closed")

def get_unimarkt_data(driver, url):
    try:
        driver.get(url)
    except:
        print("URL not available")
    time.sleep(10)

    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')

    # get breadcrumbs and categories
    breadcrumb = soup.find("ol", class_="breadcrumb")  # get categories 1,2,3 for subcategory
    categories = breadcrumb.find_all("li")
    mainCategories = {'/haushalt', '/milchprodukte', '/brot-gebaeck', '/tiefkuehl', '/obst-gemuese', '/getraenke', '/suesses-snacks', '/lebensmittel', '/fleisch-wurst'}
    categoryList = []
    notValid = ['/', ', ']
    for item in categories:
        try:
            a = item.find("a", href=True)
            category = a.get("href")
            if category not in notValid:
                categoryList.append(category)
        except:
            continue

    if not categoryList[1]:  #other urls than food subs are in url list as well...
        print("hauptkategorie...")
        return

    products = soup.find_all("div", class_="produktContainer")
    print(f"Anzahl Produkte: {len(products)}")

    for product in products:
        id = product.get("data-articleid")
        price = product.get("data-price")
        price = float(price) # MAKE it FLOATTTTTTTTTTTT!!!!!!!!!!!!!!!!!
        price_unit_long = product.find("span", class_="vergleichspreis").text.strip()
        price_regex = re.compile(r'\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})')
        try:
            price_unit = price_regex.search(price_unit_long).group().replace(",", ".")

            unit = price_unit_long.split(" / ", 1)[1]
        except:
            print("No price_unit")
            continue

        exists = db.session.query(
            db.session.query(Product).filter_by(id=id).exists()
        ).scalar()

        if exists:
            print(f"Product with  ID {id} exists.")
            print(f"Today's price is: {price}")

            newPrice = Price(price=price, price_unit=price_unit, firstDate=date,
                                          ProductID=id, latest=True)
            newPrice.add_Price()
            db.session.commit()
            continue

        title = product.find("span", class_="name").text.strip()
        brand = product.get("data-marke")
        url = product.a.get('href')
        amount = product.find("span", class_="grammatur").text.strip()

        scraped_product = Product(id=id, title=title,
                                          url=url, amount=amount, brand=brand, unit=unit, priceChanges=0, merchant="Unimarkt")

        scraped_product.category1 = categoryList[0]
        scraped_product.category2 = categoryList[1]
        try:
            scraped_product.category3 = categoryList[2]
        except:
            scraped_product.category3 = "Not available"

        scraped_product.add_Product()

        newPrice = Price(price=price, firstDate=date,
                                 ProductID=id, latest=True, price_unit=price_unit)
        newPrice.add_Price()
        print("New product and price added.")


def get_unimarkt_categories():
    mainCategories = {'/haushalt', '/milchprodukte', '/brot-gebaeck', '/tiefkuehl', '/obst-gemuese', '/getraenke', '/suesses-snacks', '/lebensmittel', '/fleisch-wurst'}
    list = []
    for category in mainCategories:
        page = requests.get('https://shop.unimarkt.at' + category)
        time.sleep(5)
        soup = BeautifulSoup(page.content, 'html.parser')
        menu = soup.find("ul", class_="level2menue")
        items = menu.find_all("li")
        for item in items:
            subitems = item.find_all("li")
            if not subitems: # if list is empty (and therfore no smaller category)add this url
                x = item.a.get("href")
                if x not in mainCategories:
                    list.append(x)
    return list


def main():

    driver = webdriver.Firefox(executable_path="./geckodriver")
    time.sleep(12)
    counter = 0
    #category urls where extracted before
    urls = ['/schwein', '/rind', '/gefluegel', '/schinken-speck', '/wurstaufschnitt', '/roh-dauerwurst-salami', '/streichwurst-grammeln-mehr', '/wuerstel', '/spezialitaeten', '/marmelade', '/honig-ahornsirup', '/haselnuss-nougatcreme', '/zucker-suessstoff', '/pudding-puddingmixtur', '/nuesse-trockenfruechte', '/dekor-glasur-streusel', '/sonstige-backartikel', '/tafeloel-rapsoel-mehr', '/olivenoel', '/essig-weinessig-mehr', '/balsamicoessig', '/dressing-salatmarinade', '/salz-salzmixtur', '/kraeuter-gewuerze', '/ketchup', '/senf', '/mayonaise', '/saucen', '/pastasaucen-sugo', '/delikatessen-welt', '/suppeneinlagen', '/nudeln-pasta', '/fertigteig-frisch', '/mehl-staerke-griess', '/huelsenfruechte-haferflocken', '/risotto-reis-reisgerichte', '/muesliriegel', '/muesli', '/cerealien', '/fleischaufstrich', '/fischkonserven', '/frucht-gemuesekonserven', '/dosengerichte', '/fertiggerichte', '/suppen-bouillon-saucen', '/basis-fixprodukte', '/beilagenmischung', '/eier', '/vegan-vegetarisch', '/nahrungsergaenzung', '/brot-gebaeck-frisch', '/aufbackbroetchen-toastbrot-schnittbrot', '/kuchen-mehlspeisen', '/semmelbroesel-knoedelbrot', '/knaeckebrot-zwieback', '/pizza-snacks', '/fertig-pfannengerichte', '/fisch-fischgerichte', '/gefluegelgerichte', '/gemuesegerichte', '/tiefkuehl-gemuese', '/kraeuter-mix', '/kartoffelprodukte', '/eis', '/beeren-mix', '/mehlspeisen', '/obst', '/gemuese', '/bio-obst-gemuese', '/trockenfruechte', '/sauerkraut-kren', '/gesichts-lippenpflege', '/koerperpflege', '/haarpflege', '/mund-zahnpflege', '/wattestaebchen-wattepads-pflaster', '/nagellackentferner', '/rasierartikel-zubehoer', '/sonnenschutz', '/verhuetung', '/damenhygiene', '/toilettartikel', '/taschentuecher', '/waschmittel', '/weichspueler', '/fleckenentferner', '/allzweck-kraftreiniger', '/spezial-kalkreiniger', '/bad-wc-reiniger', '/glasreiniger', '/geschirrreiniger-spuelmittel', '/wasserenthaerter-entkalker', '/reinigungszubehoer', '/batterien-leuchtmittel', '/kuechenrollen', '/servietten', '/saecke-folien', '/kaffeefilter', '/lufterfrischer-duftkerzen', '/insektizide', '/schuhpflege', '/weitere-haushaltsartikel', '/babynahrung-saefte', '/babypflege-windeln-zubehoer', '/bueromaterial-schulbedarf', '/tiernahrung', '/tierzubehoer', '/blumenerde-duenger', '/tafelschokolade', '/schokoriegel-schokosnacks-dragees', '/pralinen', '/kekse-keksriegel', '/waffeln-waffelmischungen', '/bonbons', '/traubenzucker', '/kaubonbons-karamellen', '/fruchtgummi', '/kaugummi', '/salzgebaeck-chips-popcorn', '/nuesse-kerne', '/mineralwasser-soda', '/wasser-mit-geschmack', '/kaffee', '/kakao', '/tee', '/eistee', '/eiskaffee-kaffeemixgetraenke', '/limonaden', '/sirup', '/energydrinks', '/smoothies-direktfruchtsaefte', '/fruchtsaefte-nektar', '/bier', '/weissbier-bockbier', '/radler', '/alkoholfreies-bier', '/weisswein', '/rotwein', '/sekt-spumante', '/prosecco-frizzante', '/alkopop', '/vodka', '/rum', '/scotch-whisky', '/kraeuterbitter', '/weinbrand-cognac', '/wermut-sherry', '/gin', '/schnaps-likoer', '/milch', '/haltbarmilch', '/milch-mix-getraenke', '/joghurt-desserts', '/obers-rahm-topfen', '/milchsnacks', '/frischkaese-aufstriche', '/weichkaese', '/schmelzkaese-schnittkaese-hartkaese', '/kaesespezialitaeten', '/butter-margarine-speisefette']

    for url in urls:
        print(f"{counter}.URL: {url}")
        completeurl = "https://shop.unimarkt.at" + url
        get_unimarkt_data(driver, completeurl)
        counter += 1


if __name__ == "__main__":
    with app.app_context():
        main()