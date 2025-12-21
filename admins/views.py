# admins/views.py

import json
from django.shortcuts import redirect, render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from gpt_engine.query_engine import ask_gpt

# 1. utils에서 만든 함수 임포트
from admins.utils import render_tab_template 

def gpt_admin_page(request):
    """Render the GPT admin chat page."""
    # 2. render 대신 render_tab_template 사용
    return render_tab_template(request, "admin/chat_admin.html")

@csrf_exempt
def gpt_admin_query(request):
    """Handle GPT query requests from the admin interface."""
    if request.method == "POST":
        data = json.loads(request.body)
        question = data.get("message")
        # vector_db 경로가 맞는지 확인 필요 (이미지에선 경로 확인 불가)
        reply = ask_gpt(question, persist_path="gpt_engine/vector_db/")
        return JsonResponse({"reply": reply})
    return JsonResponse({"error": "Only POST requests are allowed"}, status=405)

@login_required(login_url='/login/')
def dashboard_view(request):
    """Redirect to the dashboard for authenticated users."""
    print(f"User {request.user.username} accessed dashboard")
    # 대시보드 URL로 리다이렉트 (실제 뷰는 admins/app/dsboard/views.py 등에 있을 것임)
    return redirect('dsboard')

def index_view(request):
    """Handle the index page view."""
    if request.user.is_authenticated:
        return redirect('dsboard')
    else:
        return redirect('adminAuth')