from django.urls import path
from . import views

urlpatterns = [
  path('', views.index,name="statementReport"),
  path('changePdf', views.changePdf,name="changePdf"),
  path('sendMail',  views.sendMail,name="sendMail"),
]