from django.urls import path
from . import views


urlpatterns = [
    path('', views.index, name='mngVat'),  
    path('getSentMails', views.getSentMails, name='getSentMails'),
    path('sendMail', views.sendMail, name='sendMail'),
    path("send_kakao_notification", views.send_kakao_notification, name="send_kakao_notification"),
    path('kijang-member-popup/', views.kijang_member_popup, name='kijang_member_popup'),
    path('path_to_vat_admin', views.path_to_vat_admin, name='path_to_vat_admin'),
    path('path_to_file_admin', views.path_to_file_admin, name='path_to_file_admin'),

    path("mng_vat", views.mng_vat, name="mng_vat"),
    path("get_IssueVatList", views.get_IssueVatList, name="get_IssueVatList"),
    path("get_IssueVatList_Analy", views.get_IssueVatList_Analy, name="get_IssueVatList_Analy"),
    

    path("get_TraderList", views.get_TraderList, name="get_TraderList"),

    path("get_InspectVat", views.get_InspectVat, name="get_InspectVat"),
    path("get_TongVat", views.get_TongVat, name="get_TongVat"),
    path("get_Fee_data", views.get_Fee_data, name="get_Fee_data"),
    
    path("mng_vat_update", views.mng_vat_update, name="mng_vat_update"),
    path("save_clipboard_Vat", views.save_clipboard_Vat, name="save_clipboard_Vat"),
    path("save_elecfile_Vat", views.save_elecfile_Vat, name="save_elecfile_Vat"),
    path("mng_vat_jupsuSummit", views.mng_vat_jupsuSummit, name="mng_vat_jupsuSummit"),
    path("isVatNapbu", views.isVatNapbu, name="isVatNapbu"),
    path("check_yn12", views.check_yn12, name="check_yn12"),
    
]
