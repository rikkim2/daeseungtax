from django.urls import path
from . import views

urlpatterns = [
  path('', views.index,name="test"),
  path('TaxInvoice', views.TaxInvoice,name="TaxInvoice"),
  path('Htx_Scrap', views.Htx_Scrap,name="Htx_Scrap"),
  path('Issue_Vat',views.Issue_Vat,name='Issue_Vat'),
  path('MyWork',views.MyWork,name='MyWork'),
  path('Bank_Scrap',views.Bank_Scrap,name='Bank_Scrap'),
  path('SS_Kani',views.SS_Kani,name='SS_Kani'),
  path('SS_ZZMS',views.SS_ZZMS,name='SS_ZZMS'),
  path('SS_Corptax',views.SS_Corptax,name='SS_Corptax'),
  path('SS_SlipLedgr',views.SS_SlipLedgr,name='SS_SlipLedgr'),
  path('SS_Payroll',views.SS_Payroll,name='SS_Payroll'),
  path('SS_MakeAccount_MonthlyPay',views.SS_MakeAccount_MonthlyPay,name='SS_MakeAccount_MonthlyPay'),
  path('SS_MakePayDaejang',views.SS_MakePayDaejang,name='SS_MakePayDaejang'),
  path('Total_Employ',views.Total_Employ,name='Total_Employ'),

  path('Ibotax_Report',views.Ibotax_Report,name='Ibotax_Report'),  
  path('Htx_Report',views.Htx_Report,name='Htx_Report'),  
  path('File_Manage',views.File_Manage,name='File_Manage'), 

  path('Elec_Issue',views.Elec_Issue,name='Elec_Issue'), 
  path('SS_MagamEwall',views.SS_MagamEwall,name='SS_MagamEwall'), 
]

