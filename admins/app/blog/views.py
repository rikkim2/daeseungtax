from django.shortcuts import render, get_object_or_404,redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from app.models import MemAdmin
from app.models import User
from app.models import BlogCategory,BlogAuthor
from django.db.models import Q
from app.models import userProfile
from .forms import BlogPostForm
from app.models import BlogPost, BlogComment,BlogPostAttachment
from .forms import CommentForm, GuestCommentForm
from django.db.models import Max
from django.db.models import Count
import os
import imaplib
import imapclient
import email
import json
import datetime
from django.utils import timezone
from datetime import date
from bs4 import BeautifulSoup
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.db.models import Count, Prefetch
# 프로파일링
# import cProfile
# import pstats

now = datetime.datetime.now()

@login_required(login_url="/login/")
def blog_list(request):
    context = inner_blog_list(request)
    return render(request, "admin/blog.html",context)

def inner_blog_list(varReq):
    # profiler = cProfile.Profile()
    # profiler.enable()

#   strsql = "select seq_no,manage_no,bank_code,trim(bank_acct),trim(bank_pw),scrap_YN from scrap_bank_trader where bank_code='"+bankCode+"' and scrap_YN='Y'"
#   cursor = connection.cursor()
#   cursor.execute(strsql)
#   result = cursor.fetchall()
#   connection.commit()
#   connection.close()

    context={}
    mem_admin = MemAdmin.objects.get(admin_id=varReq.user.username)  
    context['memadmin'] = mem_admin 
    userprofile = userProfile.objects.filter(title=mem_admin.seq_no)
    if userprofile:    userprofile = userprofile.latest('description')
    if userprofile is not None:    context['userProfile'] = userprofile  
    
    # .select_related()를 이용한 최적화
    blog_posts_query = BlogPost.objects.select_related('author').prefetch_related(
        'comments',  
        Prefetch('attachments', queryset=BlogPostAttachment.objects.order_by('-uploaded_at'))
    )

    blog_posts = blog_posts_query.filter(is_public=True)
    if varReq.user.is_staff:        blog_posts = blog_posts_query.all()
    context['blog_posts'] = blog_posts  

    context['authors'] = get_authors_with_latest_post_date()  
    lastPost = get_latest_blog_post(blog_posts) 
    first_paragraph = extract_first_paragraph(lastPost.content)
    lastPost.content = first_paragraph
    context['lastPost'] = lastPost  
    lastpost_comments_count = lastPost.comments.count()
    context['lastpost_comments_count'] = lastpost_comments_count  
    author = lastPost.author
    context['lastPostAuthor'] = author 

    latest_attachment = lastPost.attachments.order_by('-uploaded_at').first()
    context['latest_attachment'] = latest_attachment     

    leftBlogList(varReq,context,blog_posts_query)

    # profiler.disable()
    # stats = pstats.Stats(profiler).sort_stats('cumulative')
    # stats.print_stats()
    return context

def extract_first_paragraph(content):
    soup = BeautifulSoup(content, 'html.parser')
    p_tags = soup.find_all('p')
    if p_tags:
        return str(p_tags[0].text)
    return ''

def get_latest_blog_post(blog_posts):
    latest_post = blog_posts.all().order_by('-published_date').first()
    return latest_post
def get_authors_with_latest_post_date():
    authors = BlogAuthor.objects.filter(blogposts__isnull=False).annotate(
        latest_post_date=Max('blogposts__published_date')
    ).order_by('user__username')
    return authors


@login_required(login_url="/login/")
def blog_edit(request, pk=None):
    context={}
    mem_admin = MemAdmin.objects.get(admin_id=request.user.username)  
    context['memadmin'] = mem_admin 

    userprofile = userProfile.objects.filter(title=mem_admin.seq_no)
    if userprofile:    userprofile = userprofile.latest('description')
    if userprofile is not None:    context['userProfile'] = userprofile     

    admin_names = MemAdmin.objects.filter(manage_YN='').values_list('admin_name', flat=True)
    context['admin_names'] = admin_names 

    categories = BlogCategory.objects.all()
    context['categories'] = categories  

    if pk:  # 글 수정
        post = get_object_or_404(BlogPost, pk=pk)
        attachments = post.attachments.all()
        context['attachments'] = attachments 
    else:  # 새 글 작성
        post = None

    if request.method == "POST":
        form = BlogPostForm(request.POST, instance=post)
        files = request.FILES.getlist('titleImg')  # 멀티파일 처리      
        if form.is_valid() and  request.user.is_authenticated:

            blog_post = form.save(commit=False)  # 데이터베이스에 아직 저장하지 않음
            # 현재 로그인한 사용자와 연결된 BlogAuthor 인스턴스를 가져오거나 생성합니다.
            blog_author, created = BlogAuthor.objects.get_or_create(user=request.user)
            blog_post.published_date = timezone.now()
            blog_post.author = blog_author  # 현재 로그인한 사용자와 연결된 BlogAuthor 인스턴스를 작성자로 설정
            blog_post.save()  # 이제 데이터베이스에 저장
            form.save_m2m()  # ManyToMany 필드를 저장합니다.

            # 첨부 파일 처리
            for f in files:
                BlogPostAttachment.objects.create(post=blog_post, file=f)

            return redirect('blog_list')
        else:
            print(form.errors)
            # 에러가 있는 경우, 에러 메시지를 JSON 형식으로 변환하여 템플릿에 전달
            errors_json = json.dumps(form.errors.as_json(), ensure_ascii=False)
            context["errors_json"] = errors_json
            return render(request, "admin/blog-edit.html",context)#오류시 재수정
    else:
        form = BlogPostForm(instance=post)

    context['post'] = post  
    return render(request, 'admin/blog-edit.html', context)

@csrf_exempt  # CSRF 토큰 검증 비활성화
def image_upload(request):
    if request.method == 'POST' and request.FILES:
        # image = request.FILES['upload']  # 'upload'는 CKEditor가 파일을 전송하는 데 사용하는 필드 이름
        # image_name = default_storage.save(image.name, image)
        # image_url = default_storage.url(image_name)
        image = request.FILES.get('file')
        # 이미지 파일을 임시 디렉터리나 지정된 경로에 저장하는 로직 구현
        image_url = '/some/path/' + image.name 
        print(image)
        print(image_url)
        return JsonResponse({'url': image_url})  # CKEditor가 요구하는 응답 형식
    return JsonResponse({'error': 'POST 요청에 파일이 포함되어 있지 않습니다.'}, status=400)


def blog_detail(request, pk):
    context = {}
    mem_admin = MemAdmin.objects.get(admin_id=request.user.username)  
    userprofile = userProfile.objects.filter(title=mem_admin.seq_no)
    if userprofile:    userprofile = userprofile.latest('description')
    if userprofile is not None:    context['userProfile'] = userprofile  

    # select_related와 prefetch_related를 이용한 최적화
    post = get_object_or_404(BlogPost.objects.select_related('author').prefetch_related(
        'comments',  # comments가 BlogPost와 연결된 필드라고 가정합니다.
        Prefetch('attachments', queryset=BlogPostAttachment.objects.order_by('-uploaded_at'))
    ), pk=pk)

    # post = get_object_or_404(BlogPost,  pk=pk)  # 주어진 ID에 해당하는 포스트를 가져오거나, 404 에러를 반환
    author = post.author
    comments_count = post.comments.count()
    latest_attachment = post.attachments.order_by('-uploaded_at').first() #상단이미지

    # annotate와 order_by를 사용하는 쿼리는 최적화가 필요 없지만, 필요에 따라 select_related를 추가할 수 있습니다.
    # top_posts = BlogPost.objects.select_related('author').annotate(comment_count=Count('comments')).order_by('-comment_count', '-published_date')[:10]

    # post의 카테고리와 같은 카테고리의 게시물들을 가져옴
    top_posts = BlogPost.objects.filter(category=post.category).select_related('author').annotate(
        comment_count=Count('comments')
    ).order_by('-comment_count', '-published_date')[:10]

    context['memadmin'] = mem_admin 
    context['post'] = post  
    context['author'] = post.author  
    context['comments_count'] = comments_count 
    comments = post.comments.all()
    context['comments'] = comments 
    context['latest_attachment'] = latest_attachment 
    context['top_posts'] = top_posts 

    # blog_posts_query = BlogPost.objects.select_related('author').prefetch_related(
    #     'comments',
    #     Prefetch('attachments', queryset=BlogPostAttachment.objects.order_by('-uploaded_at'))
    # )

    # blog_posts = blog_posts_query.filter(is_public=True)
    # if request.user.is_staff:
    #     blog_posts = blog_posts_query.all()

    categories_query = BlogCategory.objects.all()
    context['categories'] = categories_query

    return render(request, 'admin/blog-details.html', context)

def category_posts(request, category_id):
    context = {}
    mem_admin = MemAdmin.objects.get(admin_id=request.user.username)  
    userprofile = userProfile.objects.filter(title=mem_admin.seq_no)
    if userprofile:    userprofile = userprofile.latest('description')
    if userprofile is not None:    context['userProfile'] = userprofile  


    category = get_object_or_404(BlogCategory, id=category_id)
    posts = BlogPost.objects.filter(category=category).order_by('-published_date')
    latest_post = posts.first()
    # post = get_object_or_404(BlogPost,  pk=pk)  # 주어진 ID에 해당하는 포스트를 가져오거나, 404 에러를 반환
    author = latest_post.author
    comments_count = latest_post.comments.count()
    latest_attachment = latest_post.attachments.order_by('-uploaded_at').first() #상단이미지

    top_posts = BlogPost.objects.filter(category=category).order_by('-published_date')[:10]

    context['memadmin'] = mem_admin 
    context['post'] = latest_post  
    context['author'] = latest_post.author  
    context['comments_count'] = comments_count 
    comments = latest_post.comments.all()
    context['comments'] = comments 
    context['latest_attachment'] = latest_attachment 
    context['top_posts'] = top_posts 

    categories_query = BlogCategory.objects.all()
    context['categories'] = categories_query
    
    return render(request, 'admin/blog-details.html', context)

def leftBlogList(request, context, blog_posts):
    # 카테고리 쿼리 최적화 (prefetch와 조건부 로직 사용)
    categories_query = BlogCategory.objects.annotate(
        post_count=Count('blog_posts', filter=Q(blog_posts__is_public=True))
    ).prefetch_related('blog_posts')

    if request.user.is_staff:
        categories_query = BlogCategory.objects.annotate(post_count=Count('blog_posts')).prefetch_related('blog_posts')

    context['categories'] = categories_query

    # 모든 쿼리를 결합하여 데이터베이스 접근 횟수 최소화
    top_comment_posts = blog_posts.annotate(comment_count=Count('comments')).filter(comment_count__gt=0)
    top_comment_posts = top_comment_posts.order_by('-comment_count', '-published_date')[:8]

    # 중복 쿼리를 피하기 위해 한 번만 슬라이싱
    top_last_posts = blog_posts.order_by('-published_date')[:8]

    # `important_grade`에 인덱스를 추가하여 쿼리 속도 개선
    top_imp_posts = blog_posts.filter(
        Q(important_grade='1') | Q(important_grade='2')
    ).order_by('important_grade', '-published_date')

    # 새로운 법률 포스트 필터링
    top_newLaw_posts = blog_posts.filter(new_law=True).order_by('-published_date')

    # 결과를 context에 추가
    context['top_comment_posts'] = top_comment_posts
    context['top_last_posts'] = top_last_posts
    context['top_imp_posts'] = top_imp_posts
    context['top_newLaw_posts'] = top_newLaw_posts

    return context

@csrf_exempt
def create_comment(request, post_id):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and request.method == 'POST':
        data = json.loads(request.body)
        content = data.get('content')
        parent_id = data.get('parent_id', None)  # parent_id는 선택적

        if request.user.is_authenticated:
            post = BlogPost.objects.get(id=post_id)
            comment = BlogComment(
                post=post,
                author=request.user,  # 로그인한 사용자 할당
                content=content
            )

            if parent_id:
                # parent_id가 제공된 경우, 대댓글로 설정
                try:
                    parent_comment = BlogComment.objects.get(id=parent_id)
                    comment.parent = parent_comment
                except BlogComment.DoesNotExist:
                    return JsonResponse({'error': 'Parent comment does not exist'}, status=400)

            comment.save()
            response_data = {
                'success': True,
                'comment_id': comment.id,
                'content': comment.content,
                'author': comment.author.username,
                'author_profile_image': comment.author.profile.image_thumbnail.url if comment.author.profile.image_thumbnail else None
            }
            return JsonResponse(response_data)
        else:
            # 사용자가 인증되지 않은 경우, 오류 응답 전송
            return JsonResponse({'error': 'User is not authenticated'}, status=400)
    else:
        # 요청이 유효하지 않은 경우, 오류 응답 전송
        return JsonResponse({'error': 'Invalid request'}, status=400)

# def delete_comment(request, post_id):
#     post = get_object_or_404(BlogPost, pk=post_id)
#     post.delete()
#     context = inner_blog_list(request)
#     return render(request, "admin/blog.html",context)

def delete_comment(request, comment_id):
    comment = get_object_or_404(BlogComment, id=comment_id)
    post = comment.post  # 댓글이 속한 포스트를 가져옴
    comment.delete()
    return redirect(post.get_absolute_url())  # 댓글이 있던 포스트로 리디렉션

@login_required
def delete_attachment(request, attachment_id):

    context={}
    mem_admin = MemAdmin.objects.get(admin_id=request.user.username)  
    context['memadmin'] = mem_admin 

    userprofile = userProfile.objects.filter(title=mem_admin.seq_no)
    if userprofile:    userprofile = userprofile.latest('description')
    if userprofile is not None:    context['userProfile'] = userprofile     

    admin_names = MemAdmin.objects.filter(manage_YN='').values_list('admin_name', flat=True)
    context['admin_names'] = admin_names 

    categories = BlogCategory.objects.all()
    context['categories'] = categories  


    post = get_object_or_404(BlogPost, pk=attachment.post.id)
    attachments = post.attachments.all()
    context['attachments'] = attachments 


    attachment = get_object_or_404(BlogPostAttachment, id=attachment_id)
    
    # 여기서 권한 검사 로직을 추가할 수 있습니다.
    # 예를 들어, request.user가 attachment를 소유한 post의 작성자인지 확인합니다.
    if attachment.post.author.user.username != request.user.username:
        print(attachment.post.author)
        print(request.user)
        print(attachment.post.author != request.user)
        return HttpResponse('삭제권한 없음', status=401)
    
    # 파일과 데이터베이스 레코드 삭제
    attachment.file.delete()  # 실제 파일 삭제
    attachment.delete()  # 데이터베이스 레코드 삭제
    return render(request, "admin/blog-edit.html",context)
    # return redirect(attachment.post.get_absolute_url())  # 댓글이 있던 포스트로 리디렉션