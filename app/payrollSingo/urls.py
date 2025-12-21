from django.urls import path
from . import views

urlpatterns = [
  path('', views.index,name="vatSingo"),
  path('setPayrollYear', views.setPayrollYear,name="setPayrollYear"),
  path('path_to_wonchun', views.path_to_wonchun,name="path_to_wonchun"),

]