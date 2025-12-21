from django.urls import path
from . import views

urlpatterns = [
  path('', views.index,name="traderLedgr"),
  path('setSelectedYear', views.setSelectedYear,name="setSelectedYear"),
  path('getTraderGrid', views.getTraderGrid,name="getTraderGrid"),
  path('getTraderDetailGrid', views.getTraderDetailGrid,name="getTraderDetailGrid"),
  # path('sendMail',  views.sendMail,name="sendMail"),
]