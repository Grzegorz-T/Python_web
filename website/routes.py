import numpy as np
import pandas as pd
import html5lib
from flask import redirect, url_for, render_template, request, session, jsonify
from sqlalchemy import desc, func
from website import app, db
from website.usage_class import Member
from website.functions import update_stocks, is_number, count_profit
from website.models import Stocks, Members, Orders, StockSchema
from datetime import datetime

@app.route('/', methods=['GET', 'POST'])
def index():
	print(str(datetime.now().isoformat(' ', 'seconds')))
	member = Members.query.filter_by(id=1).one()
	if(request.method=='POST'):
		if request.form["action"] == "My stocks":
			return redirect(url_for('my_stocks'))
		if request.form["action"] == "Home":
			schema = StockSchema(many=True)
			stocks_list = schema.dump(Stocks.query.all())
			Member.stocks = stocks_list
			Member.table_ordered = 0
			return render_template('website.html', stocks = stocks_list, money = member.money, bought_stocks=Member.bought_stocks)
	else:
		update_stocks()
		Member.bought_stocks.clear()
		
		schema = StockSchema(many=True)
		a = schema.dump(Stocks.query.all())
		for j,item in enumerate(a):
			b = Orders.query.with_entities(func.sum(Orders.owned).label("mySum")).filter_by(stock_id=item['id']).first()
			if(b.mySum):
				Member.bought_stocks.update({ item['id']:{'quantity': int(b.mySum), 'value': round(item['price']*int(b.mySum),3), 'profit': 0}})
				Member.bought_stocks[item['id']]['profit'] = count_profit(item['id'])
		
		stocks_list = schema.dump(Stocks.query.all())
		Member.stocks = stocks_list
		Member.table_ordered = 0
		return render_template('website.html', stocks = stocks_list, money = member.money, bought_stocks=Member.bought_stocks)

@app.route('/mystocks', methods=['GET','POST'])
def my_stocks():
	if(request.method=='POST'):
		if request.form["action"] == "Home":
			return redirect(url_for('index'))
	else:
		member = Members.query.filter_by(id=1).one()

		schema = StockSchema(many=True)
		a = schema.dump(Stocks.query.all())
		for j,item in enumerate(a):
			b = Orders.query.with_entities(func.sum(Orders.owned).label("mySum")).filter_by(stock_id=item['id']).first()
			if(b.mySum):
				Member.bought_stocks.update({ item['id']:{'quantity': int(b.mySum), 'value': round(item['price']*int(b.mySum),3), 'profit': 0}})
				Member.bought_stocks[item['id']]['profit'] = count_profit(item['id'])

		stocks=[]
		for value in Member.bought_stocks:
			stocks.append(Stocks.query.filter_by(id=value).first())
		schema = StockSchema(many=True)
		stocks_list = schema.dump(stocks)
		Member.stocks = stocks_list
		Member.table_ordered = 0
		return render_template('website.html', stocks = stocks_list, money = member.money, bought_stocks=Member.bought_stocks)

@app.route('/process', methods=['POST'])
def counter():
	member = Members.query.filter_by(id=1).one()
	ids = int(request.form['id'])
	
	if(is_number(request.form['quantity'])):
		input = int(request.form['quantity'])
		if(input<0 or input>1000000):
			if ids in Member.bought_stocks:
				return jsonify({'money': member.money, 'quantity' : Member.bought_stocks[ids]['quantity'], 'value' : Member.bought_stocks[ids]['value'], 'profit': Member.bought_stocks[ids]['profit']})
			else:
				return jsonify({'money': member.money, 'quantity' : 0, 'value' : 0, 'profit': 0})
	else:
		if ids in Member.bought_stocks:
			return jsonify({'money': member.money, 'quantity' : Member.bought_stocks[ids]['quantity'], 'value' : Member.bought_stocks[ids]['value'], 'profit': Member.bought_stocks[ids]['profit']})
		else:
			return jsonify({'money': member.money, 'quantity' : 0, 'value' : 0, 'profit': 0})
	
	update_stocks()
	stock = Stocks.query.filter_by(id=ids).first()
	price = stock.price

	quantity = 0
	a = Orders.query.with_entities(func.sum(Orders.owned).label("mySum")).filter_by(stock_id=ids).one()
	if a.mySum:
		quantity = int(a.mySum)
	else:
		quantity = 0

	maximum=int(member.money/price)
	if(int(request.form['buy_sell'])==0):
		if(maximum!=0):
			Member.bought_stocks.update({ids:{'quantity': 0, 'value': 0, 'profit': 0}})
			if(input>maximum):
				input = maximum
		else:
			if ids in Member.bought_stocks:
				return jsonify({'money': member.money, 'quantity' : Member.bought_stocks[ids]['quantity'], 'value' : Member.bought_stocks[ids]['value'], 'profit': Member.bought_stocks[ids]['profit']})
			else:
				return jsonify({'money': member.money, 'quantity' : 0, 'value' : 0, 'profit': 0})
		
		quantity = quantity + input
		Member.bought_stocks[ids]['value'] = round(price*quantity,3)
		Member.bought_stocks[ids]['quantity'] = Member.bought_stocks[ids]['quantity'] + input
		value = round(price*quantity,3)
		member.money = round(member.money - price*input,4)
		new = Orders(1,input,input,ids,price,False,str(datetime.now().isoformat(' ', 'seconds')))
		db.session.add(new)
		db.session.commit()
		return jsonify({'money': member.money, 'quantity' : quantity, 'value' : value, 'profit': count_profit(ids)})
	
	else:
		if(input<quantity):
			quantity = quantity - input
			value = round((quantity)*price,4)
			Member.bought_stocks
			left = input
			new = Orders(1,input,0,ids,price,True,str(datetime.now().isoformat(' ', 'seconds')))
			db.session.add(new)
			while(left != 0):
				upd = Orders.query.filter(Orders.owned>0).filter_by(stock_id=ids).order_by('order_id').first()
				if(left>=upd.owned):
					left = left - upd.owned
					upd.owned = 0
				else:
					upd.owned = upd.owned - left
					left = 0
				db.session.commit()
			Member.bought_stocks[ids]['value']=value
			return jsonify({'money': member.money, 'quantity' : quantity, 'value' : value, 'profit': count_profit(ids)})

		else:
			if(quantity!=0):
				input=quantity
				tozero = Orders.query.filter(Orders.owned>0).filter_by(stock_id=ids).order_by('order_id').all()
				for item in tozero:
					item.owned = 0
				quantity = 0
				value = 0
				profit = 0
				member.money = round(member.money + price*input,4)
				del Member.bought_stocks[ids]
				new = Orders(1,input,0,ids,price,True)
				db.session.add(new)
				db.session.commit()
				return jsonify({'money': member.money, 'quantity' : quantity, 'value' : value, 'profit': profit})
			else:
				return jsonify({'money': member.money, 'quantity' : 0, 'value' : 0, 'profit': 0})


@app.route('/charts')
def charts():
	member = Members.query.filter_by(id=1).one()
	return render_template('charts.html', money = member.money)

@app.route('/_upd_charts')
def upd_charts():
	schema = StockSchema(many=True)
	a = schema.dump(Stocks.query.all())
	for j,item in enumerate(a):
		b = Orders.query.with_entities(func.sum(Orders.owned).label("mySum")).filter_by(stock_id=item['id']).first()
		if(b.mySum):
			Member.bought_stocks.update({ item['id']:{'quantity': int(b.mySum), 'value': round(item['price']*int(b.mySum),3), 'profit': 0}})
			Member.bought_stocks[item['id']]['profit'] = count_profit(item['id'])
	
	stocks=[]
	for value in Member.bought_stocks:
		stocks.append(Stocks.query.filter_by(id=value).first())
	schema = StockSchema(many=True)
	stocks_list = schema.dump(stocks)
	Member.stocks = stocks_list
	labels = []
	values = []
	for stock in stocks_list:
		labels.append(stock['name'])
	df= pd.DataFrame(Member.bought_stocks)
	values = df.loc['value'].sort_values().tolist()
	
	return jsonify({'labels': labels, 'values': values})


@app.route('/_update', methods = ['POST'])
def update():
	update_stocks()
	if(Member.bought_stocks):
		for i,item in enumerate(Member.stocks):
			if item['id'] in Member.bought_stocks:
				Member.bought_stocks[item['id']]['value']=round(Member.bought_stocks[item['id']]['quantity']*Member.stocks[i]['price'],3)
				Member.bought_stocks[item['id']]['profit']=count_profit(item['id'])
	return jsonify(stocks = Member.stocks, bought_stocks=Member.bought_stocks )

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
		return jsonify(stocks = stocks_list, bought_stocks = Member.bought_stocks)