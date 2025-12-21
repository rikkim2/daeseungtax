
from django.urls import path, re_path,include
from . import views
# from app.vat.views import vat_view

from django.conf import settings
from django.conf.urls.static import static





urlpatterns = [

    # The home page
    # path('', views.dashboard, name='dashboard'),


    path('', views.landing, name='landing'),
    path('dashboard', include("app.dashboard.urls")),
    path('chat/', include("chat.urls")),
    
    # path('admins', include("app.admins.urls")),
    ## path('index', views.pages, name='index'),
    path('companyInfo', include("app.companyInfo.urls")),
    path('proofSheet', include("app.proofSheet.urls")),
    
    path('slipLedgr', include("app.slipLedgr.urls")),
    path('traderLedgr', include("app.traderLedgr.urls")),

    path('statementBS', include("app.statementBS.urls")),
    path('statementIS', include("app.statementIS.urls")),
    path('statementMC', include("app.statementMC.urls")),
    path('statementRE', include("app.statementRE.urls")),
   
    path('vatSingo', include("app.vatSingo.urls")),
    path('vatAnaly', include("app.vatAnaly.urls")),    
    

    path('payrollSingo', include("app.payrollSingo.urls")),
    path('corpSingo', include("app.corpSingo.urls")),

    path('statementReport', include("app.statementReport.urls")),
    path('bizMail', include("app.bizMail.urls")),
       
    path('faqAI', include("app.faq.urls"),name='AI'),
    
    path('kakao',include("app.kakao.urls")),
    # 테스트페이지...완성후 삭제할 것
    path('test',include("app.test.urls")),
    path('accountGpt', include("app.accountGpt.urls")),

]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)