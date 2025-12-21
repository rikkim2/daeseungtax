var maxY = Math.max(Math.max(...saleledgrs.flat()),Math.max(...costledgrs.flat())) + 10000000
var options = {
  series: [
  {
    name: "매출액",
    data: saleledgrs.reverse()
  },
  {
    name: "비용합계",
    data: costledgrs.reverse()
  }
],
  chart: {
  height: 350,
  type: 'line',
  dropShadow: {
    enabled: true,
    color: '#000',
    top: 18,
    left: 7,
    blur: 10,
    opacity: 0.2
  },
  toolbar: {
    show: false
  }
},
colors: ['#77B6EA', '#e90909'],
dataLabels: {
  enabled: true,
  formatter: function (val) {
    return formatUnit(val);
  }
},
stroke: {
  curve: 'smooth'
},
// title: {
//   text: 'Average High & Low Temperature',
//   align: 'left'
// },
grid: {
  borderColor: '#e7e7e7',
  row: {
    colors: ['#f3f3f3', 'transparent'], // takes an array which will be repeated on columns
    opacity: 0.5
  },
},
markers: {
  size: 1
},
xaxis: {
  color: '#eee',
  tickColor: 'rgba(171, 167, 167,0.2)',
  font: {
    size: 10,
    color: '#999'
  }
},
yaxis: {
  title: {
    text: '연간매출액'
  },
  min: costledgrs[0][1],
  max: maxY,
  labels: {
    formatter: function (y) {
      return formatUnit(y);
    }
  }
},
legend: {
  position: 'top',
  horizontalAlign: 'right',
  floating: true,
  offsetY: -25,
  offsetX: -5
}
};

var chart = new ApexCharts(document.querySelector("#flotArea2"), options);
chart.render();


function formatUnit(val) {
  if (val >= 100000000) {
    // 억 단위
    return (val / 100000000).toFixed(2).replace(/\.00$/, '') + "억";
  } else if (val >= 1000000) {
    // 만 단위
    return (val / 10000).toFixed(2).replace(/\.00$/, '') + "만";
  } else {
    // 그대로 표시
    return val.toLocaleString();
  }
}

  /* flot chart  

  $(function () {
    var plot = $.plot($('#flotArea2'), [{
      data: saleledgrs.reverse(),
      label: '매출액',
      color: '#77bc21'
    }, {
      data: costledgrs.reverse(),
      label: '비용합계',
      color: '#e984b1'
    }], {
      series: {
        lines: {
          show: true,
          lineWidth: 1,
          fill: true,
          fillColor: {
            colors: [{
              opacity: 0
            }, {
              opacity: 0.3
            }]
          }
        },
        shadowSize: 0
      },
      chart: {
        id: 'flotArea2',
        height: 345,

      },
      points: {
        show: true,
      },
      legend: {
        noColumns: 1,
        position: 'nw'
      },
      grid: {
        borderWidth: 1,
        borderColor: 'rgba(171, 167, 167,0.2)',
        hoverable: true
      },
      yaxis: {
        min: costledgrs[0][1],
        max: Math.max(...saleledgrs.flat()),
        color: '#eee',
        tickColor: 'rgba(171, 167, 167,0.2)',
        font: {
          size: 10,
          color: '#999'
        },
        labels: {
          formatter: function (y) {
            y = Math.round(y/10000,0)
            return y.toLocaleString() + "만";
          }
        }
      },
      xaxis: {
        color: '#eee',
        tickColor: 'rgba(171, 167, 167,0.2)',
        font: {
          size: 10,
          color: '#999'
        }
      }
    });
  });
  */