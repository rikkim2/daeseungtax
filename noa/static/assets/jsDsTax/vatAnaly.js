
am5.ready(function() {
  var root = am5.Root.new("chartdiv");
  var data = reversedList;
  root.setThemes([
    am5themes_Animated.new(root)
  ]);
  root.numberFormatter.setAll({
    numberFormat: "#a",
    bigNumberPrefixes: [
      { "number": 1e+4, "suffix": "만" },
      { "number": 1e+6, "suffix": "백만" },
      { "number": 1e+8, "suffix": "억" }
    ],
    smallNumberPrefixes: []
  });
  var chart = root.container.children.push(am5xy.XYChart.new(root, {
    panX: true,
    panY: false,
    wheelX: "panX",
    wheelY: "zoomX",
    layout: root.verticalLayout
  }));

  //상단스크롤바
  // chart.set("scrollbarX", am5.Scrollbar.new(root, {
  //   orientation: "horizontal"
  // }));
  var xAxis = chart.xAxes.push(am5xy.CategoryAxis.new(root, {
    categoryField: "과세기간",
    renderer: am5xy.AxisRendererX.new(root, {}),
    tooltip: am5.Tooltip.new(root, {
      themeTags: ["axis"],
      animationDuration: 200
    })
  }));
  xAxis.data.setAll(data);

  var yAxis = chart.yAxes.push(am5xy.ValueAxis.new(root, {
    min: 0,
    renderer: am5xy.AxisRendererY.new(root, {})
  }));
  var zAxis = chart.yAxes.push(am5xy.ValueAxis.new(root, {
    min: 0,
    renderer: am5xy.AxisRendererY.new(root, {})
  }));

  var series0 = chart.series.push(am5xy.ColumnSeries.new(root, {
    name: "매입합계",
    xAxis: xAxis,
    yAxis: yAxis,
    valueYField: "매입합계",
    categoryXField: "과세기간",
    clustered: false,
    tooltip: am5.Tooltip.new(root, {
      labelText: "매입합계: {valueY}"
    })
  }));
  series0.columns.template.setAll({
    width: am5.percent(80),
    tooltipY: 0
  });
  series0.data.setAll(data);
  
  var series1 = chart.series.push(am5xy.ColumnSeries.new(root, {
    name: "매출합계",
    xAxis: xAxis,
    yAxis: yAxis,
    valueYField: "매출합계",
    categoryXField: "과세기간",
    clustered: false,
    tooltip: am5.Tooltip.new(root, {
      labelText: "매출합계: {valueY}"
    })
  }));
  series1.columns.template.setAll({
    width: am5.percent(50),
    tooltipY: 0
  });
  series1.data.setAll(data);

  var series2 = chart.series.push(am5xy.LineSeries.new(root, {
    name: "납부세액",
    xAxis: xAxis,
    yAxis: yAxis,
    valueYField: "납부세액",
    categoryXField: "과세기간",
    clustered: false,
    tooltip: am5.Tooltip.new(root, {
      labelText: "납부세액: {valueY}"
    })
  }));
  series2.strokes.template.setAll({ strokeWidth: 2 });
  series2.bullets.push(function() {
    return am5.Bullet.new(root, {
      sprite: am5.Circle.new(root, {
        strokeWidth: 3,
        stroke: series2.get("stroke"),
        radius: 5,
        fill: root.interfaceColors.get("background")
      })
    });
  });
  series2.data.setAll(data);  

  //색상
  series0.set("fill", am5.color(0xFF9E9B));   //매입액
  series1.set("fill", am5.color(0x87cefa));   //매출액
  series2.set("fill", am5.color(0x50b300));   //납부세액

  series1.columns.template.events.on("click", function(ev) {
    console.log("Clicked on a column", ev.target._dataItem.dataContext.과세기간);
    changeAll(ev.target._dataItem.dataContext.과세기간,ev.target._dataItem.dataContext.과세유형);
  });
  series0.columns.template.events.on("click", function(ev) {
    console.log("Clicked on a column", ev.target._dataItem.dataContext.과세기간);
    changeAll(ev.target._dataItem.dataContext.과세기간,ev.target._dataItem.dataContext.과세유형);
  });
  var cursor = chart.set("cursor", am5xy.XYCursor.new(root, {}));
  chart.appear(1000, 100);
  series0.appear();
  series1.appear();
}); // end am5.ready()
am5.addLicense("AM5C372573951");
const changeAll = (period,youhyung)=>{
  $.ajax({
    url:"{% url 'getTraderList' %}",
    data:{
      period:period,
      youhyung:youhyung
    },
    dataType:"Json",
    success: function(data){
      console.log(data)
    }//success
  });
}//const changeAll