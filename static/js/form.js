$(document).ready(function() {

	$(document).on('click','.btn-outline-success', function(event) {

		let member_id = $(this).attr('member_id');
		let quant = $('#Stock_Input'+member_id).val();
		let price = $(this).val();
		let money = $('#money').val();
		let profit = $('#profit'+member_id).val();
		req = $.ajax({
			data : {
				id: member_id,
				quantity: quant,
				value: quant*price,
				money: money-(quant*price)
			},
			type : 'POST',
			url : '/process'
		})
		req.done(function(data) {
			$('#quantity'+member_id).text('Owned: '+ data.quantity)
			$('#bought'+member_id).text('Value: '+ data.value +'$')
			$('#profit'+member_id).text(data.profit +'%')
			$('#money').text(data.money +'%')
		});

		event.preventDefault();

	});

});