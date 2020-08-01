
class Member:
	table_ordered = 0
	top_down = False
	stocks = []
	bought_stocks = {}
	cleared_orders = False

	def clear_orders_db():
		if(Member.cleared_orders==False):
			Orders.query.delete()
			Member.clear_orders=True