from django.urls import path

from . import views

urlpatterns = [
    path("", views.income_manage, name="mngIncome"),

    # ✅ 탭 내 비동기 조회(JSON)
    # path("ajax/list/", views.api_income_list, name="api_income_list"),
    # path("ajax/update/", views.ajax_income_update, name="ajax_income_update"),
    # ✅ 탭 내부 AJAX 로드용
    path("mng_income/api/list/", views.api_income_list, name="api_income_list"),

    # ✅ 셀 수정/체크 저장용
    path("mng_income/api/update/", views.api_income_update, name="ajax_income_update"),

    # path("ajax/paste-excel/", views.ajax_paste_excel_income, name="ajax_paste_excel_income"),
    # path("upload/elec-file/", views.income_upload_elec_file, name="income_upload_elec_file"),
    # path("upload/pretax/", views.income_upload_pretax, name="income_upload_pretax"),
]
