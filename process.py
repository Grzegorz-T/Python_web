import requests
import numpy as np
import pandas as pd
import html5lib
from bs4 import BeautifulSoup
from flask import Flask, redirect, url_for, render_template, request, session, jsonify
from sqlalchemy import desc, func
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
		a = Orders.query.filter(Orders.owned>0).filter_by(stock_id=i).order_by('order_id').all()
		for j in a:
			b_value += j.owned*j.purchase_price
		if(b_value!=Member.bought[i]):
				Member.profit[i] = round(((Member.bought[i] - b_value)/b_value)*100,3)
		else:
			Member.profit[i]=0
			

	'''for i in range(get_stocks_size()):
		b_value = 0
		if(len(Member.orders[i])>1):
			for j in range(len(Member.orders[i])-1):
				b_value += Member.orders[i][j][0]*Member.orders[i][j][1]
			if(b_value!=Member.bought[i]):
				Member.profit[i] = round(((Member.bought[i] - b_value)/b_value)*100,3)
			else:
				Member.profit[i]=0
		else:
			Member.profit[i]=0'''


app = Flask(__name__)
app.config['SECRET_KEY'] = 'my_secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root@localhost/web'
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

class Orders(db.Model):
	__tablename__='orders'
	order_id = db.Column('order_id', db.Integer, primary_key = True)
	member_id = db.Column('member_id', db.Integer)
	quantity = db.Column('quantity', db.Integer)
	owned = db.Column('owned', db.Integer)
	stock_id = db.Column('stock_id', db.Integer, index = True)
	purchase_price = db.Column('purchase_price', db.Float)
	buy_sell = db.Column('buy/sell', db.Boolean)

	def __init__(self, member_id, quantity, owned, stock_id, purchase_price, buy_sell):
		self.member_id = member_id
		self.quantity = quantity
		self.owned = owned
		self.stock_id = stock_id
		self.purchase_price = purchase_price
		self.buy_sell = buy_sell


class Members(db.Model):
	__tablename__='members'
	id = db.Column('id', db.Integer, primary_key = True)
	nick = db.Column('nick', db.Unicode)
	money = db.Column('money', db.Float)

	def __init__(self, id, nick, money):
		self.id = id
		self.nick = nick
		self.money = money

class StockSchema(ModelSchema):
	class Meta:
		model = Stocks

class Member:
	money = 20000
	table_ordered = 0
	top_down = False
	stocks = []
	clear_orders = False
	id = [i for i in range(255)]
	bought = [0 for i in range(get_stocks_size())]
	quant = [0 for i in range(get_stocks_size())]
	profit = [0 for i in range(get_stocks_size())]

	def clear():
		if(Member.clear_orders==False):
			Orders.query.delete()
			Member.clear_orders=True

@app.route('/', methods=['GET', 'POST'])
def index():
	member = Members.query.filter_by(id=1).one()
	if(request.method=='POST'):
		if request.form["action"] == "My Stocks":
			return redirect(url_for('my_stocks'))
		if request.form["action"] == "Home":
			schema = StockSchema(many=True)
			stocks_list = schema.dump(Stocks.query.all())
			Member.stocks = stocks_list
			Member.table_ordered = 0
			return render_template('website.html', stocks = stocks_list, money = member.money, quantity = Member.quant, bought = Member.bought, profit = Member.profit)
	else:
		update_stocks()
		for i in range(get_stocks_size()):
			a = Orders.query.with_entities(func.sum(Orders.owned).label("mySum")).filter_by(stock_id=i).first()
			if(a.mySum):
				Member.quant[i]=int(a.mySum)

		schema = StockSchema(many=True)
		stocks_list = schema.dump(Stocks.query.all())
		Member.stocks = stocks_list
		Member.table_ordered = 0
		return render_template('website.html', stocks = stocks_list, money = member.money, quantity = Member.quant, bought = Member.bought, profit = Member.profit)

@app.route('/mystocks', methods=['GET','POST'])
def my_stocks():
	if(request.method=='POST'):
		if request.form["action"] == "My Stocks":
			return redirect(url_for('index'))
		if request.form["action"] == "Home":
			return redirect(url_for('index'))
	else:
		member = Members.query.filter_by(id=1).one()
		stocks=[]
		for i, value in enumerate(Member.quant):
			if(value!=0):
				stocks.append(Stocks.query.filter_by(id=i).first())
		schema = StockSchema(many=True)
		stocks_list = schema.dump(stocks)
		Member.stocks = stocks_list
		Member.table_ordered = 0
		return render_template('website.html', stocks = stocks_list, money = member.money, quantity = Member.quant, bought = Member.bought, profit = Member.profit)

@app.route('/process', methods=['POST'])
def counter():
	input = int(request.form['quantity'])
	if(is_number(input) and input>0 and input<=1000000):
		if(int(request.form['bors'])==1):
			input = -input
		update_stocks()
		ids = int(request.form['id'])
		member = Members.query.filter_by(id=1).one()
		money = member.money
		stock = Stocks.query.filter_by(id=ids).first()
		price = stock.price

		if(input>int(money/price)):
			input = int(money/price)
		elif input<-Member.quant[ids]:
			input = -Member.quant[ids]
		Member.quant[ids] = 0

		orders = Orders.query.filter(Orders.owned>0).filter_by(stock_id=ids).order_by('order_id').all()

		if orders:
			for item in orders:
				Member.quant[ids] += item.owned
		else:
			Member.quant[ids] = 0

		if(Member.quant[ids]+input>0):
			Member.quant[ids] = Member.quant[ids] + input
			Member.bought[ids] = round(price*Member.quant[ids],3)
			member.money = round(member.money - price*input,4)

			if(input>0):
				new = Orders(1,input,input,ids,price,False)
				db.session.add(new)
				db.session.commit()
			else:
				order_value = -input
				new = Orders(1,input,0,ids,price,True)
				db.session.add(new)
				first = Orders.query.filter(Orders.owned>0).filter_by(stock_id=ids).order_by('order_id').first()

				if(first.owned!=0):

					while(order_value != 0):

						upd = Orders.query.filter(Orders.owned>0).filter_by(stock_id=ids).order_by('order_id').first()

						if(order_value>=upd.owned):
							order_value = order_value - upd.owned
							upd.owned = 0

						else:
							upd.owned = upd.quantity - order_value
							order_value = 0
						db.session.commit()
			#count_profit()
			return jsonify({'money': member.money, 'quantity' : Member.quant[ids], 'value' : Member.bought[ids], 'profit': Member.profit[ids]})
		
		else:
			zero = Orders.query.filter(Orders.owned>0).filter_by(stock_id=ids).order_by('order_id').all()
			for item in zero:
				item.owned = 0
			Member.quant[ids]= 0
			Member.bought[ids] = 0
			Member.profit[ids] = 0
			new = Orders(1,input,0,ids,price,True)
			db.session.add(new)
			member.money = round(member.money - price*input,4)
			db.session.commit()
			return jsonify({'money': member.money, 'quantity' : Member.quant[ids], 'value' : Member.bought[ids], 'profit': Member.profit[ids]})
	else:
		return render_template('website.html')

@app.route('/page')
def page():
	return render_template('form.html')

@app.route('/_update', methods = ['GET', 'POST'])
def update():
	update_stocks()
	for i,stock in enumerate(Stocks.query.all()):
		Member.bought[i] = round(stock.price*Member.quant[i],3)
		if(Member.quant[i]!=0):
			for element in Member.stocks:
				if(element['id']==i):
					element = Stocks.query.filter_by(id=i).one()
	count_profit()
	return jsonify(stocks = Member.stocks, result = time.time(), bought = Member.bought, profit = Member.profit )

@app.route('/order_table', methods = ['POST'])
def order():
	if(request.method=='POST'):
		number = request.form['name']
		Member.table_ordered = int(number)
		if(Member.table_ordered==0):
			Member.stocks = Stocks.query.all()
		elif(Member.table_ordered==1):
			if(Member.top_down==True):
				Member.stocks = sorted(Member.stocks, key=lambda k: k['name'])
				Member.top_down = False
			else:
				Member.stocks = sorted(Member.stocks, key=lambda k: k['name'], reverse=True)
				Member.top_down = True
		elif(Member.table_ordered==2):
			if(Member.top_down==True):
				Member.stocks = sorted(Member.stocks, key=lambda k: k['price'])
				Member.top_down=False
			else:
				Member.stocks = sorted(Member.stocks, key=lambda k: k['price'], reverse=True)
				Member.top_down = True
		elif(Member.table_ordered==3):
			if(Member.top_down==True):
				Member.stocks = sorted(Member.stocks, key=lambda k: k['change'])
				Member.top_down=False
			else:
				Member.stocks = sorted(Member.stocks, key=lambda k: k['change'], reverse=True)
				Member.top_down = True
		elif(Member.table_ordered==4):
			if(Member.top_down==True):
				Member.stocks = sorted(Member.stocks, key=lambda k: k['perc'])
				Member.top_down=False
			else:
				Member.stocks = sorted(Member.stocks, key=lambda k: k['perc'], reverse=True)
				Member.top_down = True
		elif(Member.table_ordered==5):
			if(Member.top_down==True):
				Member.stocks = sorted(Member.stocks, key=lambda k: k['opening'])
				Member.top_down=False
			else:
				Member.stocks = sorted(Member.stocks, key=lambda k: k['opening'], reverse=True)
				Member.top_down = True
		elif(Member.table_ordered==6):
			if(Member.top_down==True):
				Member.stocks = sorted(Member.stocks, key=lambda k: k['stock_max'])
				Member.top_down=False
			else:
				Member.stocks = sorted(Member.stocks, key=lambda k: k['stock_max'], reverse=True)
				Member.top_down = True
		else:
			if(Member.top_down==True):
				Member.stocks = sorted(Member.stocks, key=lambda k: k['stock_min'])
				Member.top_down=False
			else:
				Member.stocks = sorted(Member.stocks, key=lambda k: k['stock_min'], reverse=True)
				Member.top_down = True
		schema = StockSchema(many=True)
		stocks_list = schema.dump(Member.stocks)
		return jsonify(stocks = stocks_list, quantity = Member.quant, bought = Member.bought, profit = Member.profit)


if __name__ == '__main__':
	app.run(debug=True)