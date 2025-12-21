#from django.conf import settings  # django 프로젝트의 설정파일을 불러옵니다.
from django.urls import path, include
from django_hosts import patterns, host  # django_hosts의 urls 같은 역할입니다.

 

host_patterns = patterns(
    '',
    host('', 'noa.urls', name=''),
    host(r'www', 'noa.urls', name='www'),
    host(r'admin', 'admins.urls', name='admin'),
)

urlpatterns = [
    path('', include('noa.urls')),
    #path('', include('api.urls')),
]

urlpatterns += host_patterns

