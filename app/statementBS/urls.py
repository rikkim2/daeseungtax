from django.urls import path
from . import views

urlpatterns = [
  path('', views.index,name="statementBS"),
  path('setSelectedYear', views.setSelectedYear,name="setSelectedYear"),
  path('getStatementList', views.getStatementList,name="getStatementList"),
  path('getFinancialData', views.getFinancialData,name="getFinancialData"),
  # path('getPLFinancialData',  views.getPLFinancialData,name="getPLFinancialData"),
]