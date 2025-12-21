from django.urls import path
from . import views

urlpatterns = [
  path('', views.index,name="slipLedgr"),
  path('getKejungList',views.getKejungList,name="getKejungList"),
  path('setSelectedYear', views.setSelectedYear,name="setSelectedYear"),
  path('setLedgrGrid', views.setLedgrGrid,name="setLedgrGrid"),
  path('getLedgrDetail', views.getLedgrDetail,name="getLedgrDetail"),
  path('getLedgrMoreDetail', views.getLedgrMoreDetail,name="getLedgrMoreDetail"),
  path('getYearlyTradeDetail', views.getYearlyTradeDetail,name="getYearlyTradeDetail"),
  path('getYearlyTradeLedgr', views.getYearlyTradeLedgr,name="getYearlyTradeLedgr"),
]