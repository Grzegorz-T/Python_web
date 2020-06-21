$(document).ready(function() {

	$(document).on('click','.btn-outline-success', function(event) {

		var member_id = $(this).attr('member_id');
		var quant = $('#nameInput'+member_id).val();
		var price = $(this).val();
		var money = $('#money').val();
		req = $.ajax({
			data : {
				id: member_id,
				lol: member_id,
				value: quant*price,	
				money: money - (quant*price)
			},
			type : 'POST',
			url : '/process'
		})
		req.done(function(data) {});
		
		event.preventDefault();

	});

});