from django.urls import path
from . import views
from . import views_upload


urlpatterns = [
    path('', views.index, name='mngStat'),  
    path('getSentMails', views.getSentMails, name='getSentMails'),
    path('sendMail', views.sendMail, name='sendMail'),
    path("send_kakao_notification", views.send_kakao_notification, name="send_kakao_notification"),
    path('kijang-member-popup/', views.kijang_member_popup, name='kijang_member_popup'),
    path('tbl_mng_jaroe_update/', views.tbl_mng_jaroe_update, name='tbl_mng_jaroe_update'),

    path('mng_statement', views.mng_statement, name='mng_statement'),
    path("section0_data", views.section0_data, name="section0_data"),

    path("getFinancialData_Report", views.getFinancialData_Report, name="getFinancialData_Report"),
    path("getCompanyInfo", views.getCompanyInfo, name="getCompanyInfo"),



    path('diag/capital/list',   views.diag_capital_list,   name='diag_capital_list'),
    path('diag/capital/upsert', views.diag_capital_upsert, name='diag_capital_upsert'),
    path('diag/capital/delete', views.diag_capital_delete, name='diag_capital_delete'), 
    path('diag/capital/summary', views.diag_capital_summary, name='diag_capital_summary'),

    # ★ 분개장 엑셀 업로드 (HTML5 모달에서 호출)
    path("upload_slip_ledger_excel", views.upload_slip_ledger_excel, name="upload_slip_ledger_excel"),  
    path('upload/slip-ledger', views_upload.upload_slip_ledger_excel, name='upload_slip_ledger_excel'),
    path('upload/progress',     views_upload.get_upload_progress,    name='get_upload_progress'),
]
