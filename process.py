import requests
import numpy as np
import pandas as pd
import html5lib
from bs4 import BeautifulSoup
from flask import Flask, redirect, url_for, render_template, request, session, jsonify
from sqlalchemy import desc
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, send
import MySQLdb
from apscheduler.schedulers.background import BackgroundScheduler
import time
import webbrowser
import json
from marshmallow_sqlalchemy import ModelSchema
import marshmallow as ma

def make_soup(url):
	url = requests.get(url)
	mysoup = BeautifulSoup(url.content, 'html.parser')
	return mysoup

def get_stocks_size():
	soup = make_soup('https://www.bankier.pl/gielda/notowania/akcje')
	a = len(soup.find_all("tr"))
	return a

def get_stocks():
	soup = make_soup('https://www.bankier.pl/gielda/notowania/akcje')
	a = len(soup.find_all("tr"))
	tab = [[i] for i in range(a-1)]

	for i,record in enumerate(soup.find_all("tr")):
		for data in record.findAll("td"):
			tab[i-1].append(data.text.strip())
		if(i>0 and i!=10):
			if(tab[i-1][1]=='LPP'):
				tab[i-1][2] = tab[i-1][2].replace(u'\xa0', u'')
				tab[i-1][7] = tab[i-1][2].replace(u'\xa0', u'')
				tab[i-1][8] = tab[i-1][2].replace(u'\xa0', u'')
				tab[i-1][9] = tab[i-1][2].replace(u'\xa0', u'')
			if(i>10):
				upd = Stocks.query.filter_by(id=i-2).first()
				upd.id = i - 2
			else:
				upd = Stocks.query.filter_by(id=i-1).first()
				upd.id = i - 1
			upd.name = tab[i-1][1]
			upd.price = tab[i-1][2].replace(',','.')
			upd.change = float(tab[i-1][3].replace(',','.'))
			upd.perc = float(tab[i-1][4].replace(',','.').replace('%',''))
			upd.opening = float(tab[i-1][7].replace(',','.'))
			upd.stock_max = float(tab[i-1][8].replace(',','.'))
			upd.stock_min = float(tab[i-1][9].replace(',','.'))
	db.session.commit()
	return tab

def update_stocks():
    num = get_stocks()
    print("updated")
    return num

def is_number(n):
    try:
        int(n)
        return True
    except ValueError:
        return  False

def count_profit():
	for i in range(get_stocks_size()):
		b_value = 0
		if(len(Member.orders[i])>1):
			for j in range(len(Member.orders[i])-1):
				b_value += Member.orders[i][j][0]*Member.orders[i][j][1]
			if(b_value!=Member.bought[i]):
				Member.profit[i] = round(((Member.bought[i] - b_value)/b_value)*100,3)
		else:
			Member.profit[i]=0


app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecrets'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:root-a@localhost/website'
app.config['PRESERVE_CONTEXT_ON_EXCEPTION'] = False
app.config['SESSION_REFRESH_EACH_REQUEST'] = False
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Stocks(db.Model):
	__tablename__='stocks'
	id = db.Column('id', db.Integer, primary_key = True)
	name = db.Column('name', db.Unicode)
	price = db.Column('price', db.Float)
	change = db.Column('change', db.Float)
	perc = db.Column('perc', db.Float)
	opening = db.Column('opening', db.Float)
	stock_max = db.Column('max', db.Float)
	stock_min = db.Column('min', db.Float)

	def __init__(self, id, name, price, change, perc, opening, stock_max, stock_min):
		self.id = id
		self.name = name
		self.price = price
		self.change = change
		self.perc = perc
		self.opening = opening
		self.stock_max = stock_max
		self.stock_min = stock_min

class StockSchema(ModelSchema):
	class Meta:
		model = Stocks

class Member:
	money = 20000000
	table_ordered = 0
	top_down = True
	id = [i for i in range(255)]
	bought = [0 for i in range(get_stocks_size())]
	quant = [0 for i in range(get_stocks_size())]
	profit = [0 for i in range(get_stocks_size())]
	orders = [np.zeros([1,2]) for i in range(get_stocks_size())]

@app.route('/')
def index():
	update_stocks()
	stocks = Stocks.query.all()
	schema = StockSchema(many=True)
	stocks_list = schema.dump(stocks)
	Member.table_ordered = 0
	return render_template('website.html', stocks = stocks_list, money = Member.money, quantity = Member.quant, bought = Member.bought, profit = Member.profit)

@app.route('/process', methods=['POST'])
def counter():
	if(is_number(request.form['quantity'])):
		input = int(request.form['quantity'])

		if(input!=0 and input<=1000000 and input>=-1000000):
			update_stocks()
			ids = int(request.form['id'])
			print(ids)
			money = Member.money
			stock = Stocks.query.filter_by(id=ids).first()
			price = stock.price
			print(stock.id)
			if(input>int(money/price)):
				input = int(money/price)
			elif input<-Member.quant[ids]:
				input = -Member.quant[ids]

			if(Member.quant[ids]+input>0):
				Member.quant[ids] = Member.quant[ids] + input
				Member.bought[ids] = round(price*Member.quant[ids],3)
				Member.money = round(Member.money - price*input,4)

				if(input>0):
					Member.orders[ids]=np.insert(Member.orders[ids],len(Member.orders[ids])-1,[input,stock.price],0)
				else:
					order_value = -input
					if(Member.orders[ids][0][0]!=0):
						while(order_value != 0):
							if(order_value>=Member.orders[ids][0][0]):
								order_value = order_value - Member.orders[ids][0][0]
								Member.orders[ids]=np.delete(Member.orders[ids],0,0)
							else:
								Member.orders[ids][0][0]=Member.orders[ids][0][0]-order_value
								order_value = 0
				count_profit()
				return jsonify({'money': Member.money, 'quantity' : Member.quant[ids], 'value' : Member.bought[ids], 'money':Member.money, 'profit': Member.profit[ids]})
			
			else:
				Member.quant[ids]= 0
				Member.bought[ids] = 0
				Member.profit[ids] = 0
				Member.money = round(Member.money - price*input,4)
				Member.orders[ids]=np.zeros([1,2])
				return jsonify({'money': Member.money, 'quantity' : Member.quant[ids], 'value' : Member.bought[ids], 'money':Member.money, 'profit': Member.profit[ids]})
	
	else:
		return render_template('website.html')

@app.route('/page')
def page():
	return render_template('form.html')

@app.route('/_update', methods = ['GET', 'POST'])
def update():
	update_stocks()
	if(Member.table_ordered==0):
		stocks = Stocks.query.all()
	elif(Member.table_ordered==1):
		stocks = Stocks.query.order_by('name').all()
	elif(Member.table_ordered==2):
		stocks = Stocks.query.order_by('price').all()
	elif(Member.table_ordered==3):
		stocks = Stocks.query.order_by('change').all()
	elif(Member.table_ordered==4):
		stocks = Stocks.query.order_by('perc').all()
	elif(Member.table_ordered==5):
		stocks = Stocks.query.order_by('opening').all()
	elif(Member.table_ordered==6):
		stocks = Stocks.query.order_by('max').all()
	else:
		stocks = Stocks.query.order_by('min').all()
	schema = StockSchema(many=True)
	stocks_list = schema.dump(stocks)
	for i,stock in enumerate(Stocks.query.all()):
		Member.bought[i] = round(stock.price*Member.quant[i],3)
	count_profit()
	return jsonify(stocks = stocks_list, result = time.time(), bought = Member.bought, profit = Member.profit )

@app.route('/order_table', methods = ['GET','POST'])
def order():
	if(request.method=='POST'):
		number = request.form['name']
		Member.table_ordered = int(number)
		top_down = Member.top_down
		if(Member.table_ordered==0):
			stocks = Stocks.query.all()
		elif(Member.table_ordered==1):
			if(top_down==True):
				stocks = Stocks.query.order_by('name').all()
				top_down = False
			else:
				stocks = Stocks.query.order_by(desc('name')).all()
				top_down = True
		elif(Member.table_ordered==2):
			if(top_down==True):
				stocks = Stocks.query.order_by('price').all()
				top_down=False
			else:
				stocks = Stocks.query.order_by(desc('price')).all()
				top_down = True
		elif(Member.table_ordered==3):
			if(top_down==True):
				stocks = Stocks.query.order_by('change').all()
				top_down=False
			else:
				stocks = Stocks.query.order_by(desc('change')).all()
				top_down = True
		elif(Member.table_ordered==4):

			if(top_down==True):
				stocks = Stocks.query.order_by('perc').all()
				top_down=False
				print('tak',top_down)
			else:
				stocks = Stocks.query.order_by(desc('perc')).all()
				top_down = True
				print('nie')
		elif(Member.table_ordered==5):
			if(top_down==True):
				stocks = Stocks.query.order_by('opening').all()
				top_down=False
			else:
				stocks = Stocks.query.order_by(desc('opening')).all()
				top_down = True
		elif(Member.table_ordered==6):
			if(top_down==True):
				stocks = Stocks.query.order_by('max').all()
				top_down=False
			else:
				stocks = Stocks.query.order_by(desc('max')).all()
				top_down = True
		else:
			if(top_down==True):
				stocks = Stocks.query.order_by('min').all()
				top_down=False
			else:
				stocks = Stocks.query.order_by(desc('min')).all()
				top_down = True
		Member.top_down = top_down
		schema = StockSchema(many=True)
		stocks_list = schema.dump(stocks)
		return jsonify(stocks = stocks_list, quantity = Member.quant, bought = Member.bought, profit = Member.profit)


if __name__ == '__main__':
	app.run(debug=True)