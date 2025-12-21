from django.urls import path
from . import views


urlpatterns = [
    path('', views.index, name='mngScrap'),  
    path('scrap-monthly/', views.scrap_monthly_list, name='scrap_monthly_list'),
    path('scrap-quarter/', views.scrap_quarter_list, name='scrap_quarter_list'),
    path('scrap-card/', views.scrap_card_list, name='scrap_card_list'),
    path("update_scrap_each/", views.update_scrap_each, name="update_scrap_each"),
    path("getTISummation", views.getTISummation, name="getTISummation"),
    path("getCardSummation", views.getCardSummation, name="getCardSummation"),
    path("send_kakao_notification", views.send_kakao_notification, name="send_kakao_notification"),
    path('kijang-member-popup/', views.kijang_member_popup, name='kijang_member_popup'),
    path('sendKakao_Bulk/', views.sendKakao_Bulk, name='sendKakao_Bulk'),
]
