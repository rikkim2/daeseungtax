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