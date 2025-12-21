from django.urls import path, re_path,include
from . import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [

    path('', include("admins.app.dsboard.urls")),
    path('dsboard', include("admins.app.dsboard.urls")),
    path('auto', include("admins.app.auto.urls")), #test
    path('staffInfo', include("admins.app.staffInfo.urls")),
    path('staffList', include("admins.app.staffList.urls")),
    path('staffList2', include("admins.app.staffList2.urls")),
    path('blog/', include('admins.app.blog.urls')),
    
    path('mnguser/', include("admins.app.mnguser.urls")),
    path('mnguser', include("admins.app.mnguser.urls")),
    path('mngScrap', include("admins.app.mngScrap.urls")),
    path('mngCorp', include("admins.app.mngCorp.urls")),
    path('mngStat', include("admins.app.mngStat.urls")),
    path('mngIncome', include("admins.app.mngIncome.urls")),
    path('mngVat', include("admins.app.mngVat.urls")),
    path('mngPay', include("admins.app.mngPay.urls")),
    path("mngMsg/", include("admins.app.mngMsg.urls")),
    path('customer-autocomplete/', views.customer_autocomplete, name='customer_autocomplete'),


]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
