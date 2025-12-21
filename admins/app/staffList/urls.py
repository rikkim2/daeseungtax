from django.urls import path
from . import views
from .views import delete_admin, admin_update,admin_create



urlpatterns = [
  path('', views.index,name="staffList"),
  path('delete_admin/<int:seq_no>/', delete_admin, name='delete_admin'),
  path('admin_update/', admin_update, name='admin_update'),
  path('admin_create/', admin_create, name='admin_create'),

  path('getAdminInfo',views.getAdminInfo,name='getAdminInfo'),

  path('getInvoiceDetail/',views.getInvoiceDetail,name='getInvoiceDetail'),
  path('getSalesInvoiceDetail',views.getSalesInvoiceDetail,name='getSalesInvoiceDetail'),
  path("save-fault", views.save_fault, name="save_fault"),
  path("get-fault-data", views.get_fault_data, name="get_fault_data"),
]