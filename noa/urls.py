from django.urls import path, include
# from admins.views import login_view


urlpatterns = [

    path('',include("app.authentication.urls")),
    path('', include('app.urls')),
    
    path('accounts', include('allauth.urls')),
    path('admin/',  include('admins.urls')),
   
    # path('admins', include('admins.urls')),  ==> 장고어드민을 위해 이것을 쓰도록 하자
    # path('__debug__/', include('debug_toolbar.urls')),
]

