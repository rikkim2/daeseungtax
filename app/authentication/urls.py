from django.urls import path
from .views import login_view
from .views import forgotPassword
from django.contrib.auth.views import LogoutView

from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
  path('login/',login_view,name="login"),
  path('logout/',LogoutView.as_view(),name="logout"),
  path('login/forgotPassword',forgotPassword,name="forgotPassword"),

  # path('password_reset/', auth_views.PasswordResetView.as_view(), name="password_reset"),
  path('password_reset/', views.UserPasswordResetView.as_view(), name="password_reset"),
  path('password_reset_done/', auth_views.PasswordResetDoneView.as_view(), name="password_reset_done"),
  path('password_reset_confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
  path('password_reset_complete/', auth_views.PasswordResetCompleteView.as_view(), name="password_reset_complete"),

  path('recovery/pw/', views.RecoveryPwView.as_view(), name='recovery_pw'),
  # path('recovery/id/find/', views.ajax_find_id_view, name='ajax_id'),
  path('recovery/pw/find/', views.ajax_find_pw_view, name='ajax_pw'),
  path('recovery/pw/auth/', views.auth_confirm_view, name='recovery_auth'),
  path('recovery/pw/reset/', views.auth_pw_reset_view, name='recovery_pw_reset'),
]