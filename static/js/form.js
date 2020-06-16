$(document).ready(function() {

	$(document).on('click','.btn-outline-success', function(event) {

		var member_id = $(this).attr('member_id');
		var quant = $(this).attr('value');
		var price = $('#nameInput'+member_id).val();
		var money = $('#money').val();
		req = $.ajax({
			data : {
				id: member_id,
				name: price,
				value: quant*price,	
				money: money - (quant*price)
			},
			type : 'POST',
			url : '/process'
		})
		req.done(function(data) {
			$('#quantity'+member_id).text(data.name)
			$('#bought'+member_id).text(data.value)
		});

		event.preventDefault();

	});

});