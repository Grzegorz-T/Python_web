$(document).ready(function() {

	$(document).on('click','.btn-outline-secondary', function(event) {
        let num = $(this).attr('name');

		req = $.ajax({
            data : {
                name: num,
            },
			type : 'POST',
			url : '/order_table'
        })
        req.done(function(data) {
                $.each(data.stocks,function(i,stock){
                $('#name'+i).text(stock.name);
                $('#price'+i).text(stock.price);
                $('#perc'+i).text(stock.perc+'%');
                if(stock.change>0){
                    $('#change'+i).text(stock.change).css("color","rgb(0, 200, 0)");
                    $('#perc'+i).css("color","rgb(0, 200, 0)");
                }
                else if(stock.change==0){
                    $('#change'+i).text(stock.change);
                }
                else{
                    $('#change'+i).text(stock.change).css("color","rgb(225, 0, 0)");
                    $('#perc'+i).css("color","rgb(225, 0, 0)");
                }
                $('#opening'+i).text(stock.opening);
                $('#stock_max'+i).text(stock.stock_max);
                $('#stock_min'+i).text(stock.stock_min);
                $('#quantity'+i).text('Owned: '+data.quantity[stock.id]);
                $('#bought'+i).text('Value: '+data.bought[stock.id]+'$');
                if(data.profit[stock.id]>0){
                    $('#profit'+i).text(data.profit[stock.id]+'%').css("color","rgb(0, 200, 0)");
                }
                else if(data.profit[stock.id]==0){
                    $('#profit'+i).text(data.profit[stock.id]+'%');
                }
                else{
                    $('#profit'+i).text(data.profit[stock.id]+'%').css("color","rgb(225, 0, 0)");
                }
                $('#buy_button'+i).attr('member_id',stock.id);
                $('#sell_button'+i).attr('member_id',stock.id);
            });
        });
        event.preventDefault();
    });

});