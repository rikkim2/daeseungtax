from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from app.models import MemAdmin
from app.models import BlogPost,User
from app.models import BlogCategory,BlogAuthor
from app.models import userProfile
from django.db import connection
from django.db.models import Max

import datetime
from datetime import date
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.db.models import Count


def blog_list(request):
  context={}
  mem_admin = MemAdmin.objects.get(admin_id=request.user.username)  
  # admin_names = MemAdmin.objects.filter(manage_YN='').values_list('admin_name', flat=True)
  userprofile = userProfile.objects.filter(title=mem_admin.seq_no)
  if userprofile:    userprofile = userprofile.latest('description')
  if userprofile is not None:    context['userProfile'] = userprofile  

  blog_posts = BlogPost.objects.all()
  context['blog_posts'] = blog_posts  

  context['authors'] = get_authors_with_latest_post_date()  

  categories = BlogCategory.objects.all()
  categories = BlogCategory.objects.annotate(post_count=Count('blog_posts'))
  context['categories'] = categories  
  
  return render(request, "admin/blog.html",context)

def get_authors_with_latest_post_date():
    authors = BlogAuthor.objects.filter(blogposts__isnull=False).annotate(
        latest_post_date=Max('blogposts__published_date')
    ).order_by('user__username')
    return authors
    