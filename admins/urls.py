from django.urls import path, include
from . import views

urlpatterns = [
    # path('login/', views.login_view, name='login'),
    path('', include('admins.app.adminAuth.urls', namespace='adminAuth')),
    path('', include('admins.app.urls')),

    path("gpt_admin_query/", views.gpt_admin_query, name="gpt_admin_query"),
    path("gpt_admin_page/", views.gpt_admin_page, name="gpt_admin_page"),  # HTML 페이지    
    # path('', views.index_view, name='index'),  # Root path for the app
]

