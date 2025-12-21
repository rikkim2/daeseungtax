from django.urls import path
from . import views


urlpatterns = [
  path('', views.index,name="staffInfo"),
  path('changeSheet', views.changeSheet,name="changeSheet"),
  path('sendMailCompInfo',  views.sendMailCompInfo,name="sendMailCompInfo"),
  path('fileupload/', views.fileupload, name="fileupload"),
]