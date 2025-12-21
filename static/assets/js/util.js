function numberWithCommas(x) {
  var x2 = x*1;
  return x2.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

function isNumber(s) {
  s += ''; // 문자열로 변환
  s = s.replace(/^\s*|\s*$/g, ''); // 좌우 공백 제거
  if (s === '' || isNaN(s)) return false;
  return true;
}


// Comma 삽입호출 
function com(obj) { 
	obj.value = unComma(obj.value); 
	obj.value = Comma(obj.value); 
} 

// Comma 삽입 
function Comma(input) { 
	var inputString = new String; 
	var outputString = new String; 
	var counter = 0; 
	var decimalPoint = 0; 
	var end = 0; 
	var modval = 0; 

	inputString = input.toString(); 
	outputString = ''; 
	decimalPoint = inputString.indexOf('.', 1); 

	if(decimalPoint == -1) { 
		end = inputString.length - (inputString.charAt(0)=='0' ? 1:0); 
	
		for (counter=1;counter <=inputString.length; counter++) { 
			var modval =counter - Math.floor(counter/3)*3; 
			outputString = (modval==0 && counter <end ? ',' : '') + inputString.charAt(inputString.length - counter) + 
			outputString; 
		} 

	} else { 
		end = decimalPoint - ( inputString.charAt(0)=='-' ? 1 :0); 

		for (counter=1; counter <= decimalPoint ; counter++) { 
			outputString = (counter==0 && counter <end ? ',' : '') + inputString.charAt(decimalPoint - counter) + 
			outputString; 
		} 
		for (counter=decimalPoint; counter < decimalPoint+3; counter++) { 
			outputString += inputString.charAt(counter); 
		} 
	} 
	if (outputString=='0')
		outputString = '';
	
	return (outputString.replace('-,','-')); 
} 

// Comma 제거 
function unComma(input) { 
	var inputString = new String; 
	var outputString = new String; 
	var outputNumber = new Number; 
	var counter = 0; 

	if (input == '') { 
		return 0 
	} 

	inputString=input; 
	outputString=''; 
	for (counter=0;counter <inputString.length; counter++) { 
		outputString += (inputString.charAt(counter) != ',' ?inputString.charAt(counter) : ''); 
	} 
	outputNumber = parseFloat(outputString); 
	return (outputNumber); 
} 