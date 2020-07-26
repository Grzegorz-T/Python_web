from website import db
from marshmallow_sqlalchemy import ModelSchema
import marshmallow as ma

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



