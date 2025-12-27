from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name="dsboard"),
    path('api/pending-filings/', views.get_pending_filings, name="api_pending_filings"),
    path('api/receivables/', views.get_receivables, name="api_receivables"),
    path('api/executive-renewals/', views.get_executive_renewals, name="api_executive_renewals"),
    path('api/new-companies/', views.get_new_companies, name="api_new_companies"),
    path('api/staff-list/', views.get_staff_list, name="api_staff_list"),

    # ASP 업무 섹션 API
    path('api/bizbank/', views.get_bizbank_data, name="api_bizbank"),
    path('api/cash/', views.get_cash_data, name="api_cash"),
    path('api/vat/', views.get_vat_data, name="api_vat"),
    path('api/report/', views.get_report_data, name="api_report"),
    path('api/kani-mm/', views.get_kani_mm_data, name="api_kani_mm"),
    path('api/kani-banki/', views.get_kani_banki_data, name="api_kani_banki"),
]