from django.urls import path
from . import views

urlpatterns = [
  path('', views.index,name="statementIS"),
  path('getCostFinancialData', views.getCostFinancialData,name="getCostFinancialData"),
  # path('getTraderDetailGrid', views.getTraderDetailGrid,name="getTraderDetailGrid"),
  # path('sendMail',  views.sendMail,name="sendMail"),
]