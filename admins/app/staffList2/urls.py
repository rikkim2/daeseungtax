from django.urls import path
from . import views

urlpatterns = [
  path('', views.index,name="staffList2"),
  path('mem_admin', views.mem_admin, name='mem_admin'),
]