from django.urls import path
from . import views

urlpatterns = [
  path('', views.index,name="companyInfo"),
  path('changeSheet', views.changeSheet,name="changeSheet"),
  path('sendMailCompInfo',  views.sendMailCompInfo,name="sendMailCompInfo"),
  path('fileuploadCompanyInfo/', views.fileuploadCompanyInfo, name="fileuploadCompanyInfo"),
]