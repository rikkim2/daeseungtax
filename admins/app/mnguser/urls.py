from django.urls import path
from . import views

# app_name = 'mnguser'

urlpatterns = [
    path('', views.index, name='mnguser'),  # 기본 경로를 'mnguser'로 연결
    path('kijang-member-list/', views.kijang_member_list, name='kijang_member_list'),
    path('kijang-member-edit/', views.kijang_member_edit, name='kijang_member_edit'),
    path('kijang-admin-combolist/', views.kijang_admin_combolist, name='kijang_admin_combolist'),
    path('kijang-member-popup/', views.kijang_member_popup, name='kijang_member_popup'),
    path('kijang-member/<int:id>/', views.kijang_member_detail, name='kijang_member_detail'),
    path('kijang-member/create/', views.kijang_member_create, name='kijang_member_create'),
    path('kijang-member/<int:id>/update/', views.kijang_member_update, name='kijang_member_update'),
    path('kijang-member/<int:id>/delete/', views.kijang_member_delete, name='kijang_member_delete'),

    path('kijang/member/form/', views.kijang_member_form, name='kijang_member_form'),
    path('kijang/member/save/', views.kijang_member_save, name='kijang_member_save'),
    path('kijang/member/fileupload/', views.kijang_member_fileupload, name='kijang_member_fileupload'),
    
    path('kijang_goji_list/', views.kijang_goji_list, name='kijang_goji_list'),
    path('getMailContent/', views.getMailContent, name='getMailContent'),
    path('getSentMails', views.getSentMails, name='getSentMails'),
    path('sendMail/', views.sendMail, name='sendMail'),
    path("send_kakao_notification", views.send_kakao_notification, name="send_kakao_notification"),

    # 발송 내역 조회를 위한 경로 추가
    path("send_sms_popbill", views.send_sms_popbill, name="send_sms_popbill"),
    path("get_sms_prefill", views.get_sms_prefill, name="get_sms_prefill"),
    path("get_popbill_balance", views.get_popbill_balance, name="get_popbill_balance"),
    path('get_sent_sms_list/', views.get_sent_sms_list, name='get_sent_sms_list'),
    
]    

