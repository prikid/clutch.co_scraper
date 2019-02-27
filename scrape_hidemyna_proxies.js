// just paste this to console at https://hidemyna.me/en/proxy-list an enjoy

list = [];
$('.proxy__t tbody tr').each(function(){
	$tds = $('td', this);
	list.push(($tds.eq(4).text().indexOf('HTTPS') !==-1 ? 'https' : 'http') + '://u:p@' + $tds.eq(0).text() + ':' + $tds.eq(1).text());
});
console.log(list.join("\n"));