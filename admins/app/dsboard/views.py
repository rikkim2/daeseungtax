from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db import connection
from django.db.models import Q
from app.models import (
    MemAdmin,
    userProfile,
    MemUsers,
    부가가치세전자신고,
    부가가치세전자신고3,
    법인세전자신고2,
    원천세전자신고,
    종합소득세전자신고2,
    지급조서전자신고,
    일용직전자신고
)
import datetime
from datetime import date, timedelta
from django.utils import timezone


@login_required(login_url="/login/")
def index(request):
    """관리자 메인 대시보드 - 일정관리"""
    context = {}
    mem_admin = MemAdmin.objects.get(admin_id=request.user.username)
    userprofile = userProfile.objects.filter(title=mem_admin.seq_no)

    if userprofile:
        userprofile = userprofile.latest('description')
    if userprofile is not None:
        context['userProfile'] = userprofile

    context['memadmin'] = mem_admin
    return render(request, "admin/main-dash.html", context)


@login_required(login_url="/login/")
def get_pending_filings(request):
    """
    신고기한 3일 전까지 전자신고 접수내역이 없는 업체 리스트 조회
    담당자별로 필터링 가능
    """
    try:
        담당자 = request.GET.get('staff', None)
        today = datetime.date.today()

        # 신고 마감일 계산 함수
        def get_vat_deadline(year, period):
            """부가세 신고 마감일 계산 (1기: 4/25, 2기: 10/25)"""
            if period == '1':
                return datetime.date(year, 4, 25)
            elif period == '2':
                return datetime.date(year, 10, 25)
            return None

        def get_withholding_deadline(year, month):
            """원천세 신고 마감일 계산 (다음달 10일)"""
            if month == 12:
                return datetime.date(year + 1, 1, 10)
            else:
                return datetime.date(year, month + 1, 10)

        def get_corp_deadline(year, month):
            """법인세 신고 마감일 계산 (결산월 +3개월 말일)"""
            deadline_month = month + 3
            deadline_year = year
            if deadline_month > 12:
                deadline_month -= 12
                deadline_year += 1

            # 해당 월의 마지막 날 계산
            if deadline_month == 12:
                last_day = 31
            elif deadline_month in [4, 6, 9, 11]:
                last_day = 30
            elif deadline_month == 2:
                # 윤년 계산
                if deadline_year % 4 == 0 and (deadline_year % 100 != 0 or deadline_year % 400 == 0):
                    last_day = 29
                else:
                    last_day = 28
            else:
                last_day = 31

            return datetime.date(deadline_year, deadline_month, last_day)

        pending_list = []

        # 1. 부가가치세 미신고 업체
        current_year = today.year
        current_month = today.month

        # 부가세 기간 판단 (1기: 1-6월, 2기: 7-12월)
        if 1 <= current_month <= 6:
            vat_period = '2'  # 전년도 2기
            vat_year = current_year - 1
        else:
            vat_period = '1'  # 당해년도 1기
            vat_year = current_year

        vat_deadline = get_vat_deadline(vat_year if vat_period == '2' else current_year,
                                       '1' if vat_period == '2' else vat_period)

        if vat_deadline:
            days_until_deadline = (vat_deadline - today).days

            # 마감 3일 전부터 알림
            if -30 <= days_until_deadline <= 3:
                # 모든 일반과세자 업체 조회
                all_corps = MemUsers.objects.filter(
                    ibo_type='1',  # 일반과세자
                    del_yn='N'  # 삭제되지 않은 업체
                ).exclude(biz_no='')

                if 담당자:
                    all_corps = all_corps.filter(biz_area=담당자)

                for corp in all_corps:
                    # 해당 기간에 신고했는지 확인
                    과세기간_str = f"{vat_year}년 제{vat_period}기"

                    filed = 부가가치세전자신고3.objects.filter(
                        사업자등록번호=corp.biz_no,
                        과세기간__contains=과세기간_str
                    ).exists()

                    if not filed:
                        pending_list.append({
                            '업체명': corp.biz_name,
                            '사업자번호': corp.biz_no,
                            '담당자': corp.biz_area,
                            '신고유형': '부가가치세',
                            '과세기간': 과세기간_str,
                            '신고마감일': vat_deadline.strftime('%Y-%m-%d'),
                            'D_day': days_until_deadline,
                            '연락처': corp.biz_tel,
                            '대표자': corp.ceo_name
                        })

        # 2. 원천세 미신고 업체
        # 전월 원천세 확인 (매월 10일까지)
        if current_month == 1:
            withholding_year = current_year - 1
            withholding_month = 12
        else:
            withholding_year = current_year
            withholding_month = current_month - 1

        withholding_deadline = get_withholding_deadline(withholding_year, withholding_month)
        days_until_withholding = (withholding_deadline - today).days

        if -30 <= days_until_withholding <= 3:
            # 원천세 신고 대상 업체 (직원이 있는 업체 또는 사업소득 지급 업체)
            all_corps = MemUsers.objects.filter(
                del_yn='N'
            ).exclude(biz_no='')

            if 담당자:
                all_corps = all_corps.filter(biz_area=담당자)

            for corp in all_corps:
                과세연월_str = f"{withholding_year}{str(withholding_month).zfill(2)}"

                filed = 원천세전자신고.objects.filter(
                    사업자번호=corp.biz_no,
                    과세연월=과세연월_str
                ).exists()

                if not filed:
                    pending_list.append({
                        '업체명': corp.biz_name,
                        '사업자번호': corp.biz_no,
                        '담당자': corp.biz_area,
                        '신고유형': '원천세',
                        '과세기간': f"{withholding_year}년 {withholding_month}월",
                        '신고마감일': withholding_deadline.strftime('%Y-%m-%d'),
                        'D_day': days_until_withholding,
                        '연락처': corp.biz_tel,
                        '대표자': corp.ceo_name
                    })

        # 3. 법인세 미신고 업체 (결산월 기준)
        # 각 업체의 결산월을 확인하여 신고 마감일 계산
        all_corps = MemUsers.objects.filter(
            ibo_type='2',  # 법인
            del_yn='N'
        ).exclude(biz_no='')

        if 담당자:
            all_corps = all_corps.filter(biz_area=담당자)

        for corp in all_corps:
            # 결산월 추출 (biz_start_day에서 추정 또는 기본 12월)
            # 실제로는 별도 결산월 필드가 있어야 함
            결산월 = 12  # 기본값

            # 결산월 3개월 후가 신고 마감
            corp_deadline = get_corp_deadline(current_year - 1, 결산월)
            days_until_corp = (corp_deadline - today).days

            if -30 <= days_until_corp <= 3:
                과세년월_str = f"{current_year - 1}12"

                filed = 법인세전자신고2.objects.filter(
                    사업자번호=corp.biz_no,
                    과세년월=과세년월_str
                ).exists()

                if not filed:
                    pending_list.append({
                        '업체명': corp.biz_name,
                        '사업자번호': corp.biz_no,
                        '담당자': corp.biz_area,
                        '신고유형': '법인세',
                        '과세기간': f"{current_year - 1}년",
                        '신고마감일': corp_deadline.strftime('%Y-%m-%d'),
                        'D_day': days_until_corp,
                        '연락처': corp.biz_tel,
                        '대표자': corp.ceo_name
                    })

        # D-day 기준으로 정렬 (마감일이 가까운 순)
        pending_list.sort(key=lambda x: x['D_day'])

        return JsonResponse({
            'success': True,
            'data': pending_list,
            'count': len(pending_list)
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required(login_url="/login/")
def get_receivables(request):
    """
    미수금 현황 조회
    현재는 기본 구조만 제공, 실제 미수금 데이터는 별도 테이블 필요
    """
    try:
        담당자 = request.GET.get('staff', None)

        # TODO: 실제 미수금 테이블 연동 필요
        # 현재는 샘플 데이터 구조만 제공

        receivables = []

        # 업체별 미수금 조회 로직 (추후 구현)
        # 예시 구조:
        # query = """
        #     SELECT
        #         m.biz_name AS 업체명,
        #         m.biz_no AS 사업자번호,
        #         m.biz_area AS 담당자,
        #         SUM(계약금액 - 입금액) AS 미수금
        #     FROM MemUsers m
        #     LEFT JOIN 수임료테이블 ON ...
        #     WHERE 미수금 > 0
        #     GROUP BY ...
        # """

        return JsonResponse({
            'success': True,
            'data': receivables,
            'count': len(receivables),
            'message': '미수금 기능은 추후 구현 예정입니다.'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required(login_url="/login/")
def get_executive_renewals(request):
    """
    임원 등기 연임 안내 대상 조회
    법인 설립일 기준으로 임기 만료 예정 법인 조회
    """
    try:
        담당자 = request.GET.get('staff', None)
        today = datetime.date.today()

        renewals = []

        # 법인 업체만 조회
        corps = MemUsers.objects.filter(
            ibo_type='2',  # 법인
            del_yn='N'
        ).exclude(biz_no='')

        if 담당자:
            corps = corps.filter(biz_area=담당자)

        for corp in corps:
            # 사업 시작일 파싱
            if corp.biz_start_day and len(corp.biz_start_day) >= 8:
                try:
                    start_year = int(corp.biz_start_day[:4])
                    start_month = int(corp.biz_start_day[4:6])
                    start_day = int(corp.biz_start_day[6:8])
                    start_date = datetime.date(start_year, start_month, start_day)

                    # 임원 임기: 일반적으로 3년 (변경 가능)
                    term_years = 3

                    # 다음 연임일 계산
                    years_since_start = (today - start_date).days // 365
                    next_renewal_years = ((years_since_start // term_years) + 1) * term_years
                    next_renewal_date = datetime.date(
                        start_year + next_renewal_years,
                        start_month,
                        start_day
                    )

                    days_until_renewal = (next_renewal_date - today).days

                    # 6개월 전부터 알림
                    if 0 <= days_until_renewal <= 180:
                        renewals.append({
                            '업체명': corp.biz_name,
                            '사업자번호': corp.biz_no,
                            '담당자': corp.biz_area,
                            '대표자': corp.ceo_name,
                            '설립일': start_date.strftime('%Y-%m-%d'),
                            '연임예정일': next_renewal_date.strftime('%Y-%m-%d'),
                            'D_day': days_until_renewal,
                            '연락처': corp.biz_tel
                        })
                except (ValueError, IndexError):
                    continue

        # D-day 기준 정렬
        renewals.sort(key=lambda x: x['D_day'])

        return JsonResponse({
            'success': True,
            'data': renewals,
            'count': len(renewals)
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required(login_url="/login/")
def get_new_companies(request):
    """
    신규 업체 목록 조회
    최근 30일 이내 등록된 업체
    """
    try:
        days = int(request.GET.get('days', 30))
        담당자 = request.GET.get('staff', None)

        cutoff_date = timezone.now() - timedelta(days=days)

        query = MemUsers.objects.filter(
            reg_date__gte=cutoff_date,
            del_yn='N'
        ).exclude(biz_no='')

        if 담당자:
            query = query.filter(biz_area=담당자)

        query = query.order_by('-reg_date')

        new_companies = []
        for corp in query:
            업체유형 = '법인' if corp.ibo_type == '2' else '개인'

            new_companies.append({
                '업체명': corp.biz_name,
                '사업자번호': corp.biz_no,
                '업체유형': 업체유형,
                '담당자': corp.biz_area,
                '대표자': corp.ceo_name,
                '등록일': corp.reg_date.strftime('%Y-%m-%d %H:%M') if corp.reg_date else '',
                '연락처': corp.biz_tel,
                '이메일': corp.email,
                '업태': corp.uptae,
                '종목': corp.jongmok
            })

        return JsonResponse({
            'success': True,
            'data': new_companies,
            'count': len(new_companies)
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required(login_url="/login/")
def get_staff_list(request):
    """
    담당자 목록 조회 (필터링용)
    """
    try:
        # 담당자 목록 추출 (중복 제거)
        staff_list = MemUsers.objects.filter(
            del_yn='N'
        ).exclude(
            biz_area=''
        ).values_list('biz_area', flat=True).distinct()

        staff_list = list(staff_list)
        staff_list.sort()

        return JsonResponse({
            'success': True,
            'data': staff_list
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
