$(document).ready(function() {

	$(document).on('click','.btn-outline-success', function(event) {

		let member_id = $(this).attr('member_id');
		let row = $(this).attr('row_id');
		let quant = $('#Stock_Input'+row).val();
		let price = $('#price'+row).val();
		let money = $('#money').val();
		let profit = $('#profit'+row).val();
		req = $.ajax({
			data : {
				id: member_id,
				quantity: quant,
			},
			type : 'POST',
			url : '/process'
		})
		req.done(function(data) {
			$('#quantity'+row).text('Owned: '+ data.quantity)
			$('#bought'+row).text('Value: '+ data.value +'$')
			$('#profit'+row).text(data.profit +'%')
			$('#money').text(data.money +'%')
		});

		event.preventDefault();

	});

});