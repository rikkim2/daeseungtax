from django.urls import path
from . import views


urlpatterns = [
    # 사이드바에서 {% url 'mngMsg' %} 로 호출할 메인 엔트리
    path("", views.mngMsg, name="mngMsg"),

    path("sms/data/", views.sms_data, name="sms_data"),
    path("sms/send/", views.sms_send, name="sms_send"),

    # MAIL용 API 
    path('mail/data', views.mngMsg_mail_data, name='mngMsg_mail_data'),
    path('mail/send', views.mngMsg_mail_send, name='mngMsg_mail_send'),
    path('mail/upload', views.mngMsg_mail_upload, name='mngMsg_mail_upload'),
    path("mail/view", views.mngMsg_mail_view, name="mngMsg_mail_view"),
    path('mail/mail-targets/', views.get_mail_targets, name='get_mail_targets'),
]