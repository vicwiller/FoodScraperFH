import random
#from seleniumTry import webdriver
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

titleSelector = "productDetailsName"  # h1
priceSelector = "productDetailsPrice"  # label
articlenrSelector = "productDetailsArticleNumber"  # label
# unitSelector # not needed. included in price
price_unitSelector = "productDetailsPricePerUnit"
categorySelector = "breadcrumbContainer"  # li and href for each category How to store category?
amountSelector = "productDetailsDescription"

date = datetime.datetime.now().strftime("%Y-%m-%d")

def get_interspar_product_info(url, driver):
    time.sleep(random.randint(0, 9))
    driver.get(url)
    # dont forget to close cookie and zeitfenster
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    try:
        product_title = soup.find("h1", class_=titleSelector).text.strip()
    except:
        return "Does not exist: " + url
    article_nr = soup.find("label", class_=articlenrSelector).text.strip().replace("Artikelnummer: ", "")
    product_price_original = soup.find("label", class_=priceSelector).text.strip()
    price_regex = re.compile(r'\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})')
    product_price = price_regex.search(str(product_price_original)).group().replace(",", ".")
    price_unit = soup.find("label", class_=price_unitSelector).text.strip()
    amount = soup.find("label", class_=amountSelector).text.strip()
    print(f"Scraped product. ID: {article_nr} with TITLE: {product_title} . PRICE = {product_price} €")
    scraped_product = Product(id=article_nr, title=product_title, price=product_price,
                                       url=url, amount=amount, price_unit=price_unit)
    categories = get_interspar_category(soup)
    scraped_product.category1 = categories[0]
    scraped_product.category2 = categories[1]
    scraped_product.category3 = categories[2]

    db.session.add(scraped_product)
    db.session.commit()
    print(f"Added scraped product. ID: {article_nr} with TITLE: {product_title} . PRICE = {product_price} €")

def get_interspar_category(soup):
    container = soup.find("div", class_=categorySelector)
    breadcrumbs = container.find_all("li")
    name = ""
    categories = []
    for i in range(1, len(breadcrumbs) - 2):
        breadcrumb = breadcrumbs[i]
        a = breadcrumb.find("a", href=True)
        try:
            title = a.get('title')
        except:
            continue
        categories.append(title)
        # href = a['href']
        # hierarchy[name] = href
    return categories  # returning name for now, later hierarchy

def handle_cookie_notification(driver):
    try:
        cookie_button = driver.find_element_by_class_name("cookie-notification__button")
        cookie_button.click()
        zeitfenster_button = driver.find_element_by_class_name("back")
        zeitfenster_button.click()
    except:
        return print("Messages already closed")


def get_interspar_urls(driver, url):
    driver.get(url)
    time.sleep(10)

    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    products = soup.find_all("div", class_="productBox")
    try:
        breadcrumb = soup.find("div", class_="breadcrumb") #get categories 1,2,3 for subcategory
    except:
        return print(f"Breadcrumb not found for URL" + url)
    try:
        categories = breadcrumb.find_all("li")
    except:
        return print("Error: No breadcrumb")
    categoryList = []
    for item in categories:
        try:
            a = item.find("a", href=True)
            category = a.get("title")
            categoryList.append(category)
        except:
            continue
    print(categoryList)
    print("Number of products in category: " + str(len(products)))

    for product in products:
        try:
            link_html = product.find("a")
            link = link_html.get("href")
            article_nr = link_html.get("data-id")
        except:
            continue

        exists = db.session.query(   # check for product
            db.session.query(Product).filter_by(id=article_nr).exists()
        ).scalar()

        try:
            price = product.find("label", class_="priceInteger").text.strip() + "." + product.find("label", class_="priceDecimal").text.strip()
            price = float(price)
        except:
            continue

        price_unit_long = product.find("label", class_="extraInfoPrice").text.strip()
        price_regex = re.compile(r'\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})')
        price_unit = price_regex.search(price_unit_long).group().replace(",", ".")

        if exists:
            print(f"Product with  ID {article_nr} exists.")
            print(f"Today's price is: {price}")


            newPrice = Price(price=price, firstDate=date,
                                          ProductID=article_nr, price_unit=price_unit)
            newPrice.add_Price()
            db.session.commit()
            continue

        titles = product.find_all("div", class_="productTitle")  # there are 2 titles
        try:
            brand = titles[0].text.strip()
        except:
            continue
        title = titles[1].text.strip()
        if title == "":
            title = brand
            brand = "No Name"
        try:
            amount = product.find("div", class_="productSummary").text.strip()
        except:
            amount = "Not available"


        if "kg" in price_unit_long:
            unit = "kg"
        elif "Stück" in price_unit_long:
            unit = "Stück"
        elif "ml" in price_unit_long:
            unit = "ml"
        elif "/l" in price_unit_long:
            unit = "liter"
        else:
            unit = "Not available"

        scraped_product = Product(id=article_nr, title=title,
                                           url=link, amount=amount, brand=brand, unit=unit, priceChanges=0, merchant="Interspar")

        scraped_product.category1 = categoryList[1]
        scraped_product.category2 = categoryList[2]
        scraped_product.category3 = categoryList[3]

        scraped_product.add_Product()
        try:
            db.session.add(scraped_product)
            db.session.commit()
            print(f"Added scraped product. ID: {article_nr} with TITLE: {title} . PRICE = {price} €")
        except:
            continue

        newPrice = Price(price=price, firstDate=date,
                                         ProductID=article_nr, latest=True, price_unit=price_unit)
        newPrice.add_Price()
        print("New Price added.")

def main():
    driver = webdriver.Firefox(executable_path="./geckodriver")
    driver.get("https://www.interspar.at/shop/lebensmittel")
    time.sleep(12)
    handle_cookie_notification(driver)
    counter = 0
    urls = get_IntersparSubcategories()
    db.session.rollback()
    for url in urls:
        print(f"{counter}.URL: {url}")
        completeURL = "https://www.interspar.at" + url
        get_interspar_urls(driver, completeURL)
        counter += 1


if __name__ == "__main__":
    with app.app_context():
        main()
