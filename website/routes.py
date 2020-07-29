import numpy as np
import pandas as pd
import html5lib
from website import app, db
from website.functions import Member, get_stocks_size, update_stocks, is_number, count_profit, count_one_profit
from flask import redirect, url_for, render_template, request, session, jsonify
from website.models import Stocks, Members, Orders, StockSchema
from sqlalchemy import desc, func


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
		Member.bought_stocks.clear()
		schema = StockSchema(many=True)

		a = schema.dump(Stocks.query.all())
		for j,item in enumerate(a):
			b = Orders.query.with_entities(func.sum(Orders.owned).label("mySums")).filter_by(stock_id=item['id']).first()
			if(b.mySums):
				Member.bought_stocks.append({'id': j, 'quantity': int(b.mySums), 'bought': round(item['price']*int(b.mySums),3), 'profit': 0})
		print(Member.bought_stocks)

		for i in range(get_stocks_size()):
			a = Orders.query.with_entities(func.sum(Orders.owned).label("mySum")).filter_by(stock_id=i).first()
			if(a.mySum):
				Member.quant[i]=int(a.mySum)
		
		stocks_list = schema.dump(Stocks.query.all())
		Member.stocks = stocks_list
		Member.table_ordered = 0
		return render_template('website.html', stocks = stocks_list, money = member.money, quantity = Member.quant, bought = Member.bought, profit = Member.profit)

@app.route('/mystocks', methods=['GET','POST'])
def my_stocks():
	if(request.method=='POST'):
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

		jest=False
		if(Member.bought_stocks):
			for item in Member.bought_stocks:
				if(item['id']==ids):
					ilosc = item['quantity']
					jest = True
			if(jest==False):
				Member.bought_stocks.append({'id': ids, 'quantity': 0, 'bought': 0, 'profit': 0})
				ilosc = 0 
		else:
			Member.bought_stocks.append({'id': ids, 'quantity': 0, 'bought': 0, 'profit': 0})
			ilosc = 0

		if(input>int(money/price)):
			input = int(money/price)
		elif input<-ilosc:
			input = -ilosc
		ilosc = 0

		orders = Orders.query.filter(Orders.owned>0).filter_by(stock_id=ids).order_by('order_id').all()

		if orders:
			for item in orders:
				ilosc += item.owned
		else:
			ilosc = 0

		if(ilosc+input>0):
			ilosc = ilosc + input
			for item in Member.bought_stocks:
				if(item['id']==ids):
					item['bought'] = round(price*ilosc,3)
					item['quantity'] = item['quantity'] + input
			wartosc = round(price*ilosc,3)
			Member.bought[ids] = round(price*ilosc,3)
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
			print(Member.bought_stocks)
			return jsonify({'money': member.money, 'quantity' : ilosc, 'value' : wartosc, 'profit': count_one_profit(ids)})
		
		else:
			zero = Orders.query.filter(Orders.owned>0).filter_by(stock_id=ids).order_by('order_id').all()
			for item in zero:
				item.owned = 0
			Member.quant[ids]= 0
			Member.bought[ids] = 0
			Member.profit[ids] = 0
			ilosc = 0
			wartosc = 0
			profit = 0
			for j,item in enumerate(Member.bought_stocks):
				if(item['id']==ids):
					del Member.bought_stocks[j]
			new = Orders(1,input,0,ids,price,True)
			db.session.add(new)
			member.money = round(member.money - price*input,4)
			db.session.commit()
			return jsonify({'money': member.money, 'quantity' : ilosc, 'value' : wartosc, 'profit': profit})
	else:
		return render_template('website.html')

@app.route('/page')
def page():
	return render_template('form.html')

@app.route('/_update', methods = ['POST'])
def update():
	update_stocks()
	for i,stock in enumerate(Member.bought_stocks):
		stock['bought']=round(stock['quantity']*Member.stocks[stock['id']]['price'],3)
	for i,stock in enumerate(Member.stocks):
		Member.bought[stock['id']] = round(stock['price']*Member.quant[stock['id']],3)
	count_profit()
	return jsonify(stocks = Member.stocks, bought = Member.bought, profit = Member.profit )

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