$(document).ready(function() {

	$(document).on('click','.btn-outline-success', function(event) {

		var member_id = $(this).attr('member_id');
		var quant = $('#Stock_Input'+member_id).val();
		var price = $(this).val();
		var money = $('#money').val();
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
			$('#quantity'+member_id).text(data.quantity)
			$('#bought'+member_id).text(data.value)
			$('#money').text(data.money)
		});

		event.preventDefault();

	});

});