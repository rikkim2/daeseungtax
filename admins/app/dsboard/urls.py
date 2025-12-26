from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name="dsboard"),
    path('api/pending-filings/', views.get_pending_filings, name="api_pending_filings"),
    path('api/receivables/', views.get_receivables, name="api_receivables"),
    path('api/executive-renewals/', views.get_executive_renewals, name="api_executive_renewals"),
    path('api/new-companies/', views.get_new_companies, name="api_new_companies"),
    path('api/staff-list/', views.get_staff_list, name="api_staff_list"),
]