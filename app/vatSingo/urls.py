from django.urls import path
from . import views

urlpatterns = [
  path('', views.index,name="vatSingo"),
  path('setVatYear', views.setVatYear,name="setVatYear"),
  path('path_to_dict', views.path_to_dict,name="path_to_dict"),
  path('path_to_file', views.path_to_file,name="path_to_file"),
  path('originSizeSheet',  views.originSizeSheet,name="originSizeSheet"),

  path('vat/analy/', views.indexAnaly_view, name="vatAnaly"),
]