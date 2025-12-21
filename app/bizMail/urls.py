from django.urls import path
from . import views

urlpatterns = [
  path('', views.index,name="bizMail"),
  # path('changeSheet', views.changeSheet,name="changeSheet"),
  # path('sendMailCompInfo',  views.sendMailCompInfo,name="sendMailCompInfo"),
  # path('fileupload/', views.fileUpload, name="fileupload"),
]