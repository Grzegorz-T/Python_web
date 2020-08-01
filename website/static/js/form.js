$(document).ready(function() {

	$(document).on('click','.btn-outline-success', function(event) {

		let member_id = $(this).attr('member_id');
		let row = $(this).attr('row_id');
		let quant = $('#Stock_Input'+row).val();
		req = $.ajax({
			data : {
				id: member_id,
				quantity: quant,
				buy_sell: 0,
			},
			type : 'POST',
			url : '/process'
		})
		req.done(function(data) {
			if(quant>0){
				$('#quantity'+row).text('Owned: '+ data.quantity);
				$('#value'+row).text('Value: '+ data.value +'$');
				$('#profit'+row).text(data.profit +'%');
				$('#money').text(data.money +'$');
			}
		});

		event.preventDefault();

	});

	$(document).on('click','.btn-outline-danger', function(event) {

		let member_id = $(this).attr('member_id');
		let row = $(this).attr('row_id');
		let quant = $('#Stock_Input'+row).val();
		req = $.ajax({
			data : {
				id: member_id,
				quantity: quant,
				buy_sell: 1,
			},
			type : 'POST',
			url : '/process'
		})
		req.done(function(data) {
			if(quant>0){
				$('#quantity'+row).text('Owned: '+ data.quantity);
				$('#bought'+row).text('Value: '+ data.value +'$');
				$('#profit'+row).text(data.profit +'%');
				$('#money').text(data.money +'$').css("color","rgb(255, 193, 7)");
			}
		});

		event.preventDefault();

	});

});