from django.urls import path
from . import views


urlpatterns = [
    path('', views.index, name='mngCorp'),  
    path('getSentMails', views.getSentMails, name='getSentMails'),
    path('sendMail', views.sendMail, name='sendMail'),
    path("send_kakao_notification", views.send_kakao_notification, name="send_kakao_notification"),
    path('kijang-member-popup/', views.kijang_member_popup, name='kijang_member_popup'),
    path('tbl_mng_jaroe_update/', views.tbl_mng_jaroe_update, name='tbl_mng_jaroe_update'),



    path("mng_corp_bank", views.mng_corp_bank, name="mng_corp_bank"),

    path("mng_corp_helper", views.mng_corp_helper, name="mng_corp_helper"),
    path("mng_corp_jungki", views.mng_corp_jungki, name="mng_corp_jungki"),
    path("mng_corp_jungkan", views.mng_corp_jungkan, name="mng_corp_jungkan"),
    path("mng_corp_report", views.mng_corp_report, name="mng_corp_report"),

    path("mng_corp_update", views.mng_corp_update, name="mng_corp_update"),
    path("save_clipboard_Corp", views.save_clipboard_Corp, name="save_clipboard_Corp"),
    path("save_elecfile_Corp", views.save_elecfile_Corp, name="save_elecfile_Corp"),
    path("mng_corp_jupsuSummit", views.mng_corp_jupsuSummit, name="mng_corp_jupsuSummit"),
    
    path("mng_corp_deduct_tooltip", views.mng_corp_deduct_tooltip, name="mng_corp_deduct_tooltip"),

    path("path_to_corp_admin", views.path_to_corp_admin, name="path_to_corp_admin"),
    path('get_discount_data/', views.get_discount_data, name='get_discount_data'),
    path('update_discount_data/', views.update_discount_data, name='update_discount_data'),

    path("check_yn8/", views.check_yn8, name="check_yn8"), 
]
