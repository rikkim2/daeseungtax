from django.urls import path
from . import views

urlpatterns = [
  path('', views.index,name="dashboard"),
  # path('getMailList',  views.getMailList,name="getMailList"),

]