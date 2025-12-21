from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
  path('', views.index,name="listBlog"),
  path('get_authors_with_latest_post_date', views.get_authors_with_latest_post_date, name='get_authors_with_latest_post_date'),
  # path('image-upload/', views.image_upload, name='image_upload'),
]# + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

