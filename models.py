import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from helper import*

db = SQLAlchemy()

class Product(db.Model):
    __tablename__ = "products"
    id = db.Column(db.String, primary_key=True)
    title = db.Column(db.String, nullable=False)
    url = db.Column(db.String, nullable=True)
    unit = db.Column(db.String, nullable=True)
    category1 = db.Column(db.String, nullable=True)
    category2 = db.Column(db.String, nullable=True)
    category3 = db.Column(db.String, nullable=True)
    brand = db.Column(db.String, nullable=True)
    amount = db.Column(db.String, nullable=True)
    priceChanges = db.Column(db.Integer, nullable=False)
    prices = db.relationship("Price", backref="Product", lazy=True)
    merchant = db.Column(db.String, nullable=False)

    def add_Product(self):
        try:
            db.session.add(self)
            db.session.commit()
        except:
            print("Exists already.")

class Price(db.Model):
    __tablename__ = "prices"
    PriceID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ProductID = db.Column(db.String, db.ForeignKey("products.id"), nullable=False) #need real table name
    price = db.Column(db.FLOAT, nullable=False)
    firstDate = db.Column(db.Date, nullable=False)
    latest = db.Column(db.BOOLEAN, server_default='t', default=True) #testeb
    price_unit = db.Column(db.FLOAT, nullable=True)

    def add_Price(self):
        db.session.add(self)
        db.session.commit()

    def get_Prices(id):
        prices = db.session.query(Price.price).filter_by(ProductID=id).all()
        list = []
        for price in prices:
            x = price.price
            list.append(x)
        return list

    def update_latest(self):
        self.latest = None # when not latest anymore
        try:
            db.session.commit()
        except:
            print("Update Latest boolean failed")
