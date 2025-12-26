from django.urls import path
from django.views.generic import RedirectView
from . import views


urlpatterns = [
    path('', views.index, name='mngPay'),  

  #공통
    path('getSentMails', views.getSentMails, name='getSentMails'),
    path('sendMail', views.sendMail, name='sendMail'),
    path("send_kakao_notification", views.send_kakao_notification, name="send_kakao_notification"),
    path('kijang-member-popup/', views.kijang_member_popup, name='kijang_member_popup'),
    path("save_clipboard_Pay", views.save_clipboard_Pay, name="save_clipboard_Pay"),
    path("save_elecfile_Pay", views.save_elecfile_Pay, name="save_elecfile_Pay"),
    path('mem_deal_update/', views.mem_deal_update, name='mem_deal_update'),
  #페이지
    path("mng_payroll",   views.mng_payroll, name="mng_payroll"),
    
    path("mng_kani_kunro", views.mng_kani_kunro, name="mng_kani_kunro"),
    path("mng_zzjs_yearend", views.mng_zzjs_yearend, name="mng_zzjs_yearend"),
    path("mng_zzjs_kita", views.mng_zzjs_kita, name="mng_zzjs_kita"),
    path("mng_pay_report", views.mng_pay_report, name="mng_pay_report"),

  #내부기능
    path("pay_jupsuSummit", views.pay_jupsuSummit, name="pay_jupsuSummit"),
    path("path_to_pay", views.path_to_pay, name="path_to_pay"),
    path("get_folder_files/", views.get_folder_files, name="get_folder_files"),
    
    #사업/일용 간이지급명세서
    # 별도 뷰 없이 index 분기(flag=kaniSail)로 이동
    path("mng_kani_sa_il/", RedirectView.as_view(url="/mngPay?flag=kaniSail"), name="kani_sa_il_page"),
    path("mng_kani_sa_il/api/list/", views.api_kani_sa_il_list, name="api_kani_sa_il_list"),

    # 셀 편집 저장 (isIlyoung / YN_9 등)
    path("mng_kani_sa_il/api/update/", views.api_kani_sa_il_update, name="api_kani_sa_il_update"),

    # 엑셀 붙여넣기 저장(접수번호저장 팝업)
    path("mng_kani_sa_il/api/paste_issue/", views.api_kani_sa_il_paste_issue, name="api_kani_sa_il_paste_issue"),

    #근로소득 간이지급명세서
    # 별도 뷰 없이 index 분기(flag=kaniKunro)로 이동
    path("mng_kani_kunro/", RedirectView.as_view(url="/mngPay?flag=kaniKunro"), name="kani_kunro_page"),
    path("mng_kani_kunro/api/list/", views.api_kani_kunro_list, name="api_kani_kunro_list"),
    path("mng_kani_kunro/api/update/", views.api_kani_kunro_update, name="api_kani_kunro_update"),
]

