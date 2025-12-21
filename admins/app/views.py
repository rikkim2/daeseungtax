import datetime
from django import template
from django.db import connection
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.template import loader
from django.urls import reverse
from app.models import MemUser 
from app.models import MemDeal
from app.models import MemAdmin
from app.models import userProfile
from django.http import JsonResponse


@login_required(login_url="/login/")
def dsboard(request):

    context = {}

    return render(request, "admin/main-dash.html",context)

def customer_autocomplete(request):
    query = request.GET.get('q', '')  # 사용자 입력값을 받습니다.
    strsql = """
        SELECT a.seq_no, a.biz_no, a.ssn, a.biz_name, a.ceo_name, a.hp_no, a.tel_no,a.email, b.biz_manager ,b.kijang_YN,
        CONVERT(varchar(10), a.reg_date, 120) AS reg_date,
        b.keeping_YN,
        CONVERT(varchar(10), a.del_date, 120) AS del_date
        FROM mem_user a
        INNER JOIN mem_deal b ON a.seq_no = b.seq_no
        WHERE a.biz_name LIKE %s OR a.ceo_name LIKE %s OR a.ssn LIKE %s  OR a.biz_no LIKE %s OR a.email LIKE %s OR a.hp_no LIKE %s;
    """
    with connection.cursor() as cursor:
        cursor.execute(strsql, [f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%'])
        results = cursor.fetchall()  # 결과를 가져옴
    # 결과를 JSON 형식으로 반환
    response_data = [
        {
            'seq_no': result[0],
            'biz_no': result[1],
            'ssn': result[2],
            'biz_name': result[3],
            'ceo_name': result[4],
            'hp_no': result[5],
            'tel_no': result[6],
            'email': result[7],
            'biz_manager': result[8],
            'kijang_YN': '기장' if result[9] == 'Y' else '신고대리',
            'reg_date': result[10],
            'keeping_YN': '해임' if result[11] == 'N' else '',
            'del_date': result[12] if result[11] == 'N' else '',
        }
        for result in results
    ]
    return JsonResponse(response_data, safe=False)