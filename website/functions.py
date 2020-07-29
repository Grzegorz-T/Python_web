import requests
from bs4 import BeautifulSoup
from website import db
from website.models import Stocks, Orders

def get_stocks_size():
	url = requests.get('https://www.bankier.pl/gielda/notowania/akcje')
	soup = BeautifulSoup(url.content, 'html.parser')
	a = len(soup.find_all("tr"))
	return a

def get_stocks():
	url = requests.get('https://www.bankier.pl/gielda/notowania/akcje')
	soup = BeautifulSoup(url.content, 'html.parser')
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
			upd.price = float(tab[i-1][2].replace(',','.'))
			upd.change = float(tab[i-1][3].replace(',','.'))
			upd.perc = float(tab[i-1][4].replace(',','.').replace('%',''))
			upd.opening = float(tab[i-1][7].replace(',','.'))
			upd.stock_max = float(tab[i-1][8].replace(',','.'))
			upd.stock_min = float(tab[i-1][9].replace(',','.'))
	db.session.commit()

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

def count_one_profit(id):
	previous_value = 0
	for item in Member.bought_stocks:
		if(item['id']==id):
			current_value = item['bought']
	a = Orders.query.filter(Orders.owned>0).filter_by(stock_id=id).order_by('order_id').all()
	for j in a:
		previous_value += j.owned*j.purchase_price
		profit = round(((current_value - previous_value)/previous_value)*100,3)
	return profit
			


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

class Member:
	table_ordered = 0
	top_down = False
	stocks = []
	bought_stocks = []
	clear_orders = False
	bought = [0 for i in range(get_stocks_size())]
	quant = [0 for i in range(get_stocks_size())]
	profit = [0 for i in range(get_stocks_size())]

	def clear():
		if(Member.clear_orders==False):
			Orders.query.delete()
			Member.clear_orders=True