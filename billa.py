from selenium import webdriver
from bs4 import BeautifulSoup
import requests
import datetime
from models import *
import re
import time
import json

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

titleSelector = "productDetailsName"  # h1
priceSelector = "productDetailsPrice"  # label
articlenrSelector = "productDetailsArticleNumber"  # label
# unitSelector # not needed. included in price
price_unitSelector = "productDetailsPricePerUnit"
categorySelector = "breadcrumbs"  # li and href for each category How to store category?
amountSelector = "productDetailsDescription"

date = datetime.datetime.now().strftime("%Y-%m-%d")


def get_billa_data(driver, url):
    try:
        driver.get(url) #request the url with Selenium. Needs to be a category page.
    except:
        print("URL not available")
    time.sleep(10)

    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')

    try:
        breadcrumb = soup.find("nav", class_="breadcrumbs")  # get categories 1,2,3 for subcategory
        items = breadcrumb.find_all("li")
    except:
        print("Error: No breadcrumbs")

    products = soup.find_all("article", class_="product")
    print(f"Anzahl Produkte: {len(products)}")

    for product in products:
        json_string = product.find("button").attrs["data-dd-facebook-pixel-data"] #not working anymore. Already edited on the website
        json_string = json_string.replace("\'", "\"")
        jsondata = json.loads(json_string)

        id = jsondata["content_ids"]
        price = jsondata["value"]
        price = float(price)

        try:
            price_unit_long = product.find("div", class_="product__price-mesure")
            unit = price_unit_long.find("abbr").text.strip()
            price_unit_long_string = price_unit_long.text.strip()
            price_unit = price_unit_long_string.split(unit, 1)[1]  # with euro sign
            price_regex = re.compile(r'\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})')
            price_unit = price_regex.search(price_unit).group().replace(",", ".")
        except:
            unit = "Not available"
            price_unit = 0



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


        title = jsondata["content_name"]
        brand = "tbd" #product.get("data-marke") # was extracted later on

        url = product.find("a").get("href")
        amountString = product.find("div", class_="product__content-title")
        amount = amountString.find("span").text.strip()
        scraped_product = Product(id=id, title=title,
                                          url=url, amount=amount, brand=brand, unit=unit, priceChanges=0, merchant="Billa")

        scraped_product.category1 = items[1].text.strip()
        scraped_product.category2 = items[2].text.strip()
        try:
            scraped_product.category3 = items[3].text.strip()
        except:
            scraped_product.category3 = "Not available"

        scraped_product.add_Product()

        newPrice = Price(price=price, firstDate= date,
                                 ProductID=id, latest=True, price_unit=price_unit)
        newPrice.add_Price()
        print("New Product added.")

def main():
    driver = webdriver.Firefox(executable_path="./geckodriver")
    counter = 0
    #articleGroupIDs were extracted berfore
    articleGroupID = ['B2-443', 'B2-696', 'B2-314', 'B2-444', 'B2-881', 'B2-811', 'B2-637', 'B2-673', 'B2-641', 'B2-922', 'B2-245', 'B2-132', 'B2-931', 'B2-666', 'B2-481', 'B2-951', 'B2-441', 'B2-623', 'B2-532', 'B2-624', 'B2-663', 'B2-982', 'B2-873', 'B2-459', 'B2-992', 'B2-537', 'B2-759', 'B2-491', 'B2-932', 'B2-449', 'B2-357', 'B2-681', 'B2-612', 'B2-458', 'B2-962', 'B2-512', 'B2-634', 'B2-842', 'B2-756', 'B2-943', 'B2-665', 'B2-542', 'B2-658', 'B2-892', 'B2-112', 'B2-312', 'B2-535', 'B2-821', 'B2-865', 'B2-752', 'B2-333', 'B2-316', 'B2-489', 'B2-686', 'B2-652', 'B2-822', 'B2-884', 'B2-412', 'B2-321', 'B2-318', 'B2-639', 'B2-864', 'B2-753', 'B2-242', 'B2-757', 'B2-664', 'B2-633', 'B2-653', 'B2-445', 'B2-483', 'B2-743', 'B2-823', 'B2-485', 'B2-448', 'B2-356', 'B2-513', 'B2-572', 'B2-642', 'B2-942', 'B2-317', 'B2-111', 'B2-883', 'B2-411', 'B2-754', 'B2-452', 'B2-455', 'B2-684', 'B2-543', 'B2-582', 'B2-372', 'B2-691', 'B2-744', 'B2-322', 'B2-751', 'B2-912', 'B2-484', 'B2-415', 'B2-685', 'B2-457', 'B2-861', 'B2-611', 'B2-745', 'B2-891', 'B2-123', 'B2-961', 'B2-361', 'B2-654', 'B2-351', 'B2-671', 'B2-131', 'B2-622', 'B2-953', 'B2-824', 'B2-319', 'B2-492', 'B2-456', 'B2-354', 'B2-741', 'B2-687', 'B2-843', 'B2-632', 'B2-662', 'B2-862', 'B2-113', 'B2-413', 'B2-659', 'B2-342', 'B2-362', 'B2-635', 'B2-482', 'B2-222', 'B2-812', 'B2-490', 'B2-657', 'B2-446', 'B2-621', 'B2-487', 'B2-758', 'B2-813', 'B2-893', 'B2-949', 'B2-993', 'B2-241', 'B2-247', 'B2-683', 'B2-625', 'B2-983', 'B2-994', 'B2-121', 'B2-325', 'B2-755', 'B2-363', 'B2-672', 'B2-331', 'B2-925', 'B2-651', 'B2-863', 'B2-370', 'B2-454', 'B2-488', 'B2-841', 'B2-694', 'B2-311', 'B2-332', 'B2-223', 'B2-534', 'B2-693', 'B2-315', 'B2-872', 'B2-533', 'B2-571', 'B2-871', 'B2-453', 'B2-462', 'B2-486', 'B2-742', 'B2-631', 'B2-583', 'B2-531', 'B2-371', 'B2-434', 'B2-353', 'B2-991', 'B2-221', 'B2-246', 'B2-874', 'B2-414', 'B2-447', 'B2-435', 'B2-341', 'B2-343', 'B2-692', 'B2-358', 'B2-882', 'B2-695', 'B2-655', 'B2-323', 'B2-511', 'B2-638', 'B2-211', 'B2-451', 'B2-243', 'B2-442', 'B2-212', 'B2-122', 'B2-432', 'B2-313', 'B2-244', 'B2-352', 'B2-636', 'B2-324', 'B2-541', 'B2-461', 'B2-981', 'B2-355', 'B2-536', 'B2-581', 'B2-656', 'B2-682', 'B2-952', 'B2-114', 'B2-661']
    articleGroupID2 = ["B2-14", "B2-23", "B2-25", "B2-42", "B2-47", "B2-4A", "B2-4C", "B2-55", "B2-56", "B2-73", "B2-83",
                 "B2-8B", "B2-8C", "B2-8D", "B2-97", "B2-9C", "B2-9E", "B2-9F", "B2-9G", "B2-A3", "B2-A4", "B2-E20",
                 "B2-E21"]
    allGroups = articleGroupID + articleGroupID2

    for articleGroup in allGroups:
        url = "https://www.billa.at/warengruppe/" + articleGroup
        print(f"{counter}.URL: {url}")
        get_billa_data(driver, url)
        counter += 1


if __name__ == "__main__":
    with app.app_context():
        main()