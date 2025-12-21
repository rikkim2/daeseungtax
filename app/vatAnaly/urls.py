from django.urls import path
from . import views

urlpatterns = [
  path('', views.index,name="vatAnaly"),
  path('getTraderList', views.getTraderList,name="getTraderList"),
  path('get_QuarteredGraph', views.get_QuarteredGraph,name="get_QuarteredGraph"),
  path('get_monthly_comparison', views.get_monthly_comparison,name="get_monthly_comparison"),
  
]