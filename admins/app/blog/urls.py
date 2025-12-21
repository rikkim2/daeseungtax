from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
  path('', views.blog_list, name='blog_list'),
  
  path('blog_list', views.blog_list, name='blog_list'),
  path('blog/new/', views.blog_edit, name='blog_new'),#최초 새글 업로드시 사용
  # path('create_post', views.create_post, name='create_post'),#포스트 생성시 
  # path('blog/<int:post_id>/', views.blog_detail, name='blog_detail'),
  path('blog/<int:pk>/', views.blog_detail, name='blog_detail'),
  path('category/<int:category_id>/', views.category_posts, name='category_posts'),

  # path('blog/<int:post_id>/edit/', views.blog_edit, name='blog_edit'),
  path('blog/<int:pk>/edit/', views.blog_edit, name='blog_edit'),
  path('blog/<int:pk>/delete/', views.blog_edit, name='blog_delete'),

  path('blog/<int:post_id>/comment/', views.create_comment, name='create_comment'),
  path('blog/delete/<int:comment_id>/', views.delete_comment, name='delete_comment'),

  path('blog/<int:attachment_id>/attachment/', views.delete_attachment, name='delete_attachment'),
  
  path('image-upload/', views.image_upload, name='image_upload'),



] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

