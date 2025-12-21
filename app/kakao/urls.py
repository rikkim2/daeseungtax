from django.urls import path
from . import views

urlpatterns = [
    # path('', views.kakao_view, name='kakao'),
    path('', views.index, name='kakao'),
    path('getKKOTraderList', views.getKKOTraderList,name="getKKOTraderList"),
    path('getTiTrderSumGrid', views.getTiTrderSumGrid,name="getTiTrderSumGrid"),
    path('getTIDetailGrid', views.getTIDetailGrid,name="getTIDetailGrid"),
    path('getCardTrderSumGrid', views.getCardTrderSumGrid,name="getCardTrderSumGrid"),
    path('getCardDetailGrid', views.getCardDetailGrid,name="getCardDetailGrid"),    
]