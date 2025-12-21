from django.urls import path
from . import views

urlpatterns = [
  path('', views.index,name="corpSingo"),
  path('setCorpYear', views.setCorpYear,name="setCorpYear"), 
  path('path_to_corp', views.path_to_corp,name="path_to_corp"), 
]