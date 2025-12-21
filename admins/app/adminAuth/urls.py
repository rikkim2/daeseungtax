from django.urls import path
from .views import login_view
from .views import CustomLogoutView
# from .views import forgotPassword
from django.contrib.auth.views import LogoutView
from . import views
from django.contrib.auth import views as auth_views
app_name = 'adminAuth'  # URL namespace for adminAuth


urlpatterns = [
  path('login/', login_view, name='login'),
  # path('logout/',LogoutView.as_view(),name="logout"),
  path('logout/', CustomLogoutView.as_view(), name="logout"),


]


