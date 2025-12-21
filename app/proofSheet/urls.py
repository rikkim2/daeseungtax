from django.urls import path
from . import views
#print("프루프.url")

#root_dir = 'static/cert_DS/비앤지'
urlpatterns = [
    path('', views.index_proofSheet,name="proofSheet"),
    path('setProofYears2',views.setProofYears2,name="setProofYears2"),
    path('setSelectedProofYear', views.setSelectedProofYear,name="setSelectedProofYear"),
    #path('setFileGrid/<path>/', views.setFileGrid,name="setFileGrid"),
    path('setFileGrid', views.setFileGrid,name="setFileGrid"),
]