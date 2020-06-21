import requests
import numpy as np
import pandas as pd
import html5lib
from bs4 import BeautifulSoup
from flask import Flask, redirect, url_for, render_template, request, session, jsonify
from flask_sqlalchemy import SQLAlchemy
import pymysql
pymysql.install_as_MySQLdb()
from apscheduler.schedulers.background import BackgroundScheduler
import time
import datetime

def make_soup(url):
	url = requests.get(url)
	mysoup = BeautifulSoup(url.content, 'html.parser')
	return mysoup

def get_stocks_size():
	soup = make_soup('https://www.bankier.pl/gielda/notowania/akcje')
	size = len(soup.find_all("tr"))
	return size

def get_stocks():
	soup = make_soup('https://www.bankier.pl/gielda/notowania/akcje')
	a = len(soup.find_all("tr"))
	tab = [[i] for i in range(a-1)]

	for i,record in enumerate(soup.find_all("tr")):
		for j,data in enumerate(record.findAll("td")):
			tab[i-1].append(data.text.strip())
		if(i>1 and i!=10):
			if(tab[i-1][1]=='LPP'):
				tab[i-1][2] = tab[i-1][2].replace(u'\xa0', u'')
			if(i>10):
				upd = Stocks.query.filter_by(id=i-2).first()
				upd.id = i-2
			else:
				upd = Stocks.query.filter_by(id=i-1).first()
				upd.id = i-1
			upd.name = tab[i-1][1]
			upd.price = tab[i-1][2]
			upd.change = tab[i-1][3]
			upd.perc = tab[i-1][4]
			upd.opening = tab[i-1][7]
			upd.stock_max = tab[i-1][8]
			upd.stock_min = tab[i-1][9]
			upd.price_dot = float(tab[i-1][2].replace(',','.'))

	db.session.commit()
	return tab

def update_stocks():
    num = get_stocks()
    print("updated")
    return num


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:root-a@localhost/test'
db = SQLAlchemy(app)

class Stocks(db.Model):
	__tablename__='stocks'
	id = db.Column('id', db.Integer, primary_key = True)
	name = db.Column('name', db.Unicode)
	price = db.Column('price', db.Integer)
	change = db.Column('change', db.Unicode)
	perc = db.Column('perc', db.Unicode)
	opening = db.Column('opening', db.Unicode)
	stock_max = db.Column('max', db.Unicode)
	stock_min = db.Column('min', db.Unicode)
	price_dot = db.Column('price_dot', db.Integer)

	def __init__(self, id, name, price, change, perc, opening, stock_max, stock_min, price_dot):
		self.id = id
		self.name = name
		self.price = price
		self.change = change
		self.perc = perc
		self.opening = opening
		self.stock_max = stock_max
		self.stock_min = stock_min
		self.price_dot = price_dot

class Member:
	money = 20000
	max_orders = 200
	id = [i for i in range(255)]
	bought = [0 for i in range(get_stocks_size())]
	quant = [0 for i in range(get_stocks_size())]
	profit = [0 for i in range(get_stocks_size())]
	orders = [[[0 for i in range(2)]for i in range(200)]for i in range(get_stocks_size())]

@app.route('/')
def index():
	update_stocks()
	stocks = Stocks.query.all()
	for i,stock in enumerate(stocks):
		Member.bought[i] = round(stock.price_dot*Member.quant[i],2)
	money = Member.money
	quantity = Member.quant
	bought = Member.bought
	return render_template('website.html', stocks=stocks, money = money, quantity = quantity, bought = bought)

@app.route('/process', methods=['POST'])
def counter():
	update_stocks()
	input = int(request.form['quantity'])
	if(input!=0 and input<=100000 and input>=-100000):
		ids = int(request.form['id'])
		money = Member.money
		stock = Stocks.query.filter_by(id=ids).first()
		price = stock.price_dot

		if(input>int(money/price)):
			input = int(money/price)
		elif input<-Member.quant[ids]:
			input = -Member.quant[ids]

		if(Member.quant[ids]+input>=0):
			Member.quant[ids] = Member.quant[ids] + input
			Member.bought[ids] = round(price*Member.quant[ids],2)
			Member.money = round(Member.money - price*input,4)
			return jsonify({'money': Member.money, 'quantity' : Member.quant[ids], 'value' : Member.bought[ids]})
		
		else:
			Member.money = round(Member.money - price*input,4)
			Member.quant[ids]= 0
			Member.bought[ids] = 0
			return jsonify({'money': Member.money, 'quantity' : Member.quant[ids], 'value' : Member.bought[ids]})
	else:
		return render_template('website.html')

@app.route('/page')
def page():
	return render_template('form.html')

if __name__ == '__main__':
	app.run(debug=True)
	