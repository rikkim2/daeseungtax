from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db import connection
from django.db.models import Q
from app.models import (
    MemAdmin,
    userProfile,
    MemUsers,
    MemDeal,
    부가가치세전자신고,
    부가가치세전자신고3,
    법인세전자신고2,
    원천세전자신고,
    종합소득세전자신고2,
    지급조서전자신고,
    지급조서간이소득,
    일용직전자신고
)
import datetime
import os
from datetime import date, timedelta
from django.utils import timezone
from django.conf import settings


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
        current_year = today.year
        current_month = today.month

        # 유틸리티 함수들
        def get_month_last_day(year, month):
            """해당 월의 마지막 날 계산"""
            if month == 12:
                last_day = 31
            elif month in [4, 6, 9, 11]:
                last_day = 30
            elif month == 2:
                # 윤년 계산
                if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0):
                    last_day = 29
                else:
                    last_day = 28
            else:
                last_day = 31
            return last_day

        def adjust_for_weekend(target_date):
            """주말인 경우 다음 평일로 조정 (공휴일 간단 처리)"""
            # 토요일(5)이면 월요일로, 일요일(6)이면 월요일로
            weekday = target_date.weekday()
            if weekday == 5:  # 토요일
                target_date += timedelta(days=2)
            elif weekday == 6:  # 일요일
                target_date += timedelta(days=1)
            return target_date

        pending_list = []

        # 1. 부가가치세 미신고 업체
        # 법인(biz_type ≤ 3): 매분기말 익월 25일
        # 개인(biz_type ≥ 4): 매반기말 익월 25일

        # 법인 - 분기별 체크 (1, 4, 7, 10월 마감)
        corp_vat_quarters = {
            1: (current_year - 1, 10, 12, '4'),  # 1월: 전년 10-12월 (4분기)
            2: (current_year - 1, 10, 12, '4'),
            3: (current_year - 1, 10, 12, '4'),
            4: (current_year, 1, 3, '1'),        # 4월: 당해 1-3월 (1분기)
            5: (current_year, 1, 3, '1'),
            6: (current_year, 1, 3, '1'),
            7: (current_year, 4, 6, '2'),        # 7월: 당해 4-6월 (2분기)
            8: (current_year, 4, 6, '2'),
            9: (current_year, 4, 6, '2'),
            10: (current_year, 7, 9, '3'),       # 10월: 당해 7-9월 (3분기)
            11: (current_year, 7, 9, '3'),
            12: (current_year, 7, 9, '3'),
        }

        # 개인 - 반기별 체크 (1, 7월 마감)
        indiv_vat_periods = {
            1: (current_year - 1, 2, '2'),   # 1월: 전년 하반기 (7-12월)
            2: (current_year - 1, 2, '2'),
            3: (current_year - 1, 2, '2'),
            4: (current_year - 1, 2, '2'),
            5: (current_year - 1, 2, '2'),
            6: (current_year - 1, 2, '2'),
            7: (current_year, 1, '1'),       # 7월: 당해 상반기 (1-6월)
            8: (current_year, 1, '1'),
            9: (current_year, 1, '1'),
            10: (current_year, 1, '1'),
            11: (current_year, 1, '1'),
            12: (current_year, 1, '1'),
        }

        # 법인 부가세 체크
        if current_month in corp_vat_quarters:
            vat_year, start_month, end_month, quarter = corp_vat_quarters[current_month]
            # 분기 마지막 달의 다음달 25일
            deadline_month = end_month + 1 if end_month < 12 else 1
            deadline_year = vat_year if end_month < 12 else vat_year + 1
            vat_deadline = datetime.date(deadline_year, deadline_month, 25)
            vat_deadline = adjust_for_weekend(vat_deadline)

            days_until_deadline = (vat_deadline - today).days

            if -30 <= days_until_deadline <= 3:
                # 법인 업체 조회 (biz_type ≤ 3)
                corps = MemUsers.objects.filter(
                    del_yn='N',
                    biz_type__lte=3
                ).exclude(biz_no='')

                if 담당자:
                    corps = corps.filter(biz_area=담당자)

                for corp in corps:
                    과세기간_str = f"{vat_year}년 제{quarter}분기"

                    filed = 부가가치세전자신고3.objects.filter(
                        사업자등록번호=corp.biz_no,
                        과세기간__contains=f"{vat_year}년"
                    ).filter(
                        과세기간__contains=f"제{quarter}"
                    ).exists()

                    if not filed:
                        pending_list.append({
                            '업체명': corp.biz_name,
                            '사업자번호': corp.biz_no,
                            '담당자': corp.biz_area,
                            '신고유형': '부가가치세(법인)',
                            '과세기간': 과세기간_str,
                            '신고마감일': vat_deadline.strftime('%Y-%m-%d'),
                            'D_day': days_until_deadline,
                            '연락처': corp.biz_tel,
                            '대표자': corp.ceo_name
                        })

        # 개인 부가세 체크
        if current_month in indiv_vat_periods:
            vat_year, period_num, period_str = indiv_vat_periods[current_month]
            # 반기 마지막 달의 다음달 25일
            deadline_month = 1 if period_str == '2' else 7  # 2기는 1월 25일, 1기는 7월 25일
            deadline_year = vat_year + 1 if period_str == '2' else vat_year
            vat_deadline = datetime.date(deadline_year, deadline_month, 25)
            vat_deadline = adjust_for_weekend(vat_deadline)

            days_until_deadline = (vat_deadline - today).days

            if -30 <= days_until_deadline <= 3:
                # 개인 업체 조회 (biz_type ≥ 4)
                corps = MemUsers.objects.filter(
                    del_yn='N',
                    biz_type__gte=4
                ).exclude(biz_no='')

                if 담당자:
                    corps = corps.filter(biz_area=담당자)

                for corp in corps:
                    과세기간_str = f"{vat_year}년 제{period_str}기"

                    filed = 부가가치세전자신고3.objects.filter(
                        사업자등록번호=corp.biz_no,
                        과세기간__contains=과세기간_str
                    ).exists()

                    if not filed:
                        pending_list.append({
                            '업체명': corp.biz_name,
                            '사업자번호': corp.biz_no,
                            '담당자': corp.biz_area,
                            '신고유형': '부가가치세(개인)',
                            '과세기간': 과세기간_str,
                            '신고마감일': vat_deadline.strftime('%Y-%m-%d'),
                            'D_day': days_until_deadline,
                            '연락처': corp.biz_tel,
                            '대표자': corp.ceo_name
                        })

        # 2. 원천세 미신고 업체 (매월 10일까지)
        if current_month == 1:
            withholding_year = current_year - 1
            withholding_month = 12
        else:
            withholding_year = current_year
            withholding_month = current_month - 1

        # 다음달 10일
        if withholding_month == 12:
            withholding_deadline = datetime.date(withholding_year + 1, 1, 10)
        else:
            withholding_deadline = datetime.date(withholding_year, withholding_month + 1, 10)

        withholding_deadline = adjust_for_weekend(withholding_deadline)
        days_until_withholding = (withholding_deadline - today).days

        if -30 <= days_until_withholding <= 3:
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

        # 3. 법인세 미신고 업체 (결산월 + 3/4개월)
        # MemDeal.fiscalMM 기준
        all_corps = MemUsers.objects.filter(
            ibo_type='2',  # 법인
            del_yn='N'
        ).exclude(biz_no='')

        if 담당자:
            all_corps = all_corps.filter(biz_area=담당자)

        for corp in all_corps:
            try:
                # MemDeal에서 결산월 정보 가져오기
                mem_deal = MemDeal.objects.filter(seq_no=corp.seq_no).first()

                if not mem_deal or not mem_deal.fiscalmm:
                    continue  # 결산월 정보가 없으면 스킵

                결산월 = int(mem_deal.fiscalmm)

                # TODO: 성실신고법인 여부 확인 필요 (현재는 일반법인으로 처리)
                # 성실신고법인인 경우 +4개월, 아니면 +3개월
                is_sincere = False  # 추후 필드 추가 필요
                months_to_add = 4 if is_sincere else 3

                # 결산월 기준으로 신고연도 계산
                # 예: 결산월이 12월이면 전년도 12월 결산
                if 결산월 >= current_month - months_to_add:
                    # 전년도 결산
                    filing_year = current_year - 1
                else:
                    # 당해년도 결산
                    filing_year = current_year

                # 신고 마감일: 결산월 + months_to_add 개월의 말일
                deadline_month = 결산월 + months_to_add
                deadline_year = filing_year

                if deadline_month > 12:
                    deadline_month -= 12
                    deadline_year += 1

                last_day = get_month_last_day(deadline_year, deadline_month)
                corp_deadline = datetime.date(deadline_year, deadline_month, last_day)
                corp_deadline = adjust_for_weekend(corp_deadline)

                days_until_corp = (corp_deadline - today).days

                # 마감일 전후 30일 이내만 체크
                if -30 <= days_until_corp <= 30:
                    과세년월_str = f"{filing_year}{str(결산월).zfill(2)}"

                    filed = 법인세전자신고2.objects.filter(
                        사업자번호=corp.biz_no,
                        과세년월=과세년월_str
                    ).exists()

                    if not filed:
                        신고유형 = '법인세(성실)' if is_sincere else '법인세'
                        pending_list.append({
                            '업체명': corp.biz_name,
                            '사업자번호': corp.biz_no,
                            '담당자': corp.biz_area,
                            '신고유형': 신고유형,
                            '과세기간': f"{filing_year}년 {결산월}월 결산",
                            '신고마감일': corp_deadline.strftime('%Y-%m-%d'),
                            'D_day': days_until_corp,
                            '연락처': corp.biz_tel,
                            '대표자': corp.ceo_name
                        })
            except (ValueError, AttributeError):
                continue

        # 4. 종합소득세 미신고 업체 (개인사업자, 매년 5월/6월 말)
        # 일반: 5월 31일, 성실신고대상자: 6월 30일
        if 4 <= current_month <= 7:  # 4월~7월에만 체크
            # 개인사업자 조회 (biz_type ≥ 4)
            all_corps = MemUsers.objects.filter(
                del_yn='N',
                biz_type__gte=4
            ).exclude(biz_no='')

            if 담당자:
                all_corps = all_corps.filter(biz_area=담당자)

            for corp in all_corps:
                # TODO: 성실신고대상자 여부 확인 필요
                is_sincere = False  # 추후 필드 추가 필요

                # 일반: 5월 31일, 성실: 6월 30일
                deadline_month = 6 if is_sincere else 5
                last_day = get_month_last_day(current_year, deadline_month)
                income_deadline = datetime.date(current_year, deadline_month, last_day)
                income_deadline = adjust_for_weekend(income_deadline)

                days_until_income = (income_deadline - today).days

                # 마감일 전후 30일 이내만 체크
                if -30 <= days_until_income <= 30:
                    과세년도_str = str(current_year - 1)

                    filed = 종합소득세전자신고2.objects.filter(
                        주민번호__contains=corp.ssn[:6] if corp.ssn else '',
                        과세년월__contains=과세년도_str
                    ).exists()

                    if not filed:
                        신고유형 = '종합소득세(성실)' if is_sincere else '종합소득세'
                        pending_list.append({
                            '업체명': corp.biz_name,
                            '사업자번호': corp.biz_no,
                            '담당자': corp.biz_area,
                            '신고유형': 신고유형,
                            '과세기간': f"{current_year - 1}년",
                            '신고마감일': income_deadline.strftime('%Y-%m-%d'),
                            'D_day': days_until_income,
                            '연락처': corp.biz_tel,
                            '대표자': corp.ceo_name
                        })

        # 5. 지급조서간이소득 미신고 업체 (매월 간이지급명세서)
        # 제출기한: 이번달 분은 다음달 말일까지
        # 전월 지급조서 확인 (다음달 말일 마감)

        # 전월 계산
        if current_month == 1:
            filing_month = 12
            filing_year = current_year - 1
        else:
            filing_month = current_month - 1
            filing_year = current_year

        # 이번달 말일이 마감일
        if current_month == 12:
            next_month = 1
            next_year = current_year + 1
        else:
            next_month = current_month + 1
            next_year = current_year

        # 마감일: 이번달 말일 계산
        if current_month in [1, 3, 5, 7, 8, 10, 12]:
            last_day = 31
        elif current_month in [4, 6, 9, 11]:
            last_day = 30
        else:  # 2월
            # 윤년 계산
            if current_year % 4 == 0 and (current_year % 100 != 0 or current_year % 400 == 0):
                last_day = 29
            else:
                last_day = 28

        filing_deadline = datetime.date(current_year, current_month, last_day)
        days_until_filing = (filing_deadline - today).days

        # 이번달 말일 전후 5일 이내만 체크
        if -5 <= days_until_filing <= last_day:
            # 모든 업체 조회
            all_corps = MemUsers.objects.filter(
                del_yn='N'
            ).exclude(biz_no='')

            if 담당자:
                all_corps = all_corps.filter(biz_area=담당자)

            for corp in all_corps:
                # 전월 원천세 신고가 있는지 확인
                과세연월_str = f"{filing_year}{str(filing_month).zfill(2)}"

                # 원천세 신고 확인
                원천세_신고 = 원천세전자신고.objects.filter(
                    사업자번호=corp.biz_no,
                    과세연월=과세연월_str
                ).first()

                # 원천세 신고가 있는 업체만 체크
                if 원천세_신고:
                    # 지급조서간이소득 신고 여부 확인 (같은 월)
                    과세년월_str = f"{filing_year}{str(filing_month).zfill(2)}"

                    지급조서_신고 = 지급조서간이소득.objects.filter(
                        사업자번호=corp.biz_no,
                        과세년도__contains=str(filing_year)
                    ).first()

                    # 지급조서 신고가 없거나, 있어도 해당 월 데이터가 없는 경우
                    # (간이지급명세서는 매월 제출하므로 접수일시로 확인)
                    needs_filing = False

                    if not 지급조서_신고:
                        needs_filing = True
                    else:
                        # 접수일시를 확인하여 해당 월에 신고했는지 체크
                        if 지급조서_신고.접수일시:
                            접수일시_str = str(지급조서_신고.접수일시)
                            # 접수일시에 해당 년월이 포함되어 있는지 확인
                            if 과세연월_str not in 접수일시_str:
                                needs_filing = True
                        else:
                            needs_filing = True

                    if needs_filing:
                        pending_list.append({
                            '업체명': corp.biz_name,
                            '사업자번호': corp.biz_no,
                            '담당자': corp.biz_area,
                            '신고유형': '지급조서(간이)',
                            '과세기간': f"{filing_year}년 {filing_month}월",
                            '신고마감일': filing_deadline.strftime('%Y-%m-%d'),
                            'D_day': days_until_filing,
                            '연락처': corp.biz_tel,
                            '대표자': corp.ceo_name,
                            '비고': '원천세 신고 있음'
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


# ==================== ASP 업무 섹션 API ====================

@login_required(login_url="/login/")
def get_bizbank_data(request):
    """
    1. 사업용계좌 미신고 업체 조회
    """
    print("\n" + "="*80)
    print("[사업용계좌 API] 요청 시작")
    print("="*80)

    try:
        담당자 = request.GET.get('staff', None)
        admin_id = request.user.username

        print(f"📥 요청 파라미터:")
        print(f"  - admin_id: {admin_id}")
        print(f"  - 담당자 필터: {담당자 or '전체'}")

        sql = """
            SELECT a.seq_no AS sqno, a.biz_name, b.biz_manager
            FROM mem_user a
            LEFT OUTER JOIN mem_deal b ON a.seq_no = b.seq_no
            LEFT OUTER JOIN mem_admin c ON b.biz_manager = c.admin_id
            LEFT OUTER JOIN 사업용계좌신고현황 d ON d.seq_no = a.seq_no
            WHERE a.seq_no = b.seq_no
                AND a.Del_YN <> 'Y'
                AND b.biz_manager = c.admin_id
                AND b.manage_YN = 'Y'
                AND a.duzon_ID <> ''
                AND b.keeping_YN = 'Y'
                AND b.kijang_YN = 'Y'
                AND a.biz_type > 3
                AND d.seq_no IS NULL
        """

        if admin_id != 'AAAAA':
            sql += " AND c.admin_name = %s"
            params = [admin_id]
        else:
            params = []

        if 담당자:
            sql += " AND b.biz_manager = %s"
            params.append(담당자)

        sql += " AND b.biz_manager NOT IN ('환급1','종소세','종소세1','종소세2','종소세3') ORDER BY b.biz_manager"

        print(f"\n🔍 SQL 쿼리:")
        print(f"  Params: {params}")
        print(f"  Query Preview: {sql[:200]}...")

        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            rows = cursor.fetchall()

        print(f"\n✅ 쿼리 실행 성공!")
        print(f"  - 조회된 행 수: {len(rows)}")

        result = []
        for row in rows:
            result.append([row[0], row[2], row[1]])  # [sqno, biz_manager, biz_name]

        print(f"  - 결과 데이터 샘플: {result[:3] if result else '데이터 없음'}")
        print(f"\n✅ 응답 성공 (200 OK)")
        print("="*80 + "\n")

        return JsonResponse({
            'success': True,
            'data': result,
            'count': len(result)
        })

    except Exception as e:
        import traceback
        print(f"\n❌ 에러 발생!")
        print(f"  에러 메시지: {str(e)}")
        print(f"\n상세 스택 트레이스:")
        print(traceback.format_exc())
        print("="*80 + "\n")

        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required(login_url="/login/")
def get_cash_data(request):
    """
    2. 현금영수증 가맹점 가입의무 현황
    """
    print("\n" + "="*80)
    print("[현금영수증 API] 요청 시작")
    print("="*80)

    try:
        담당자 = request.GET.get('staff', None)
        year = request.GET.get('year', datetime.datetime.now().year)
        admin_id = request.user.username

        print(f"📥 요청 파라미터:")
        print(f"  - admin_id: {admin_id}")
        print(f"  - 담당자 필터: {담당자 or '전체'}")
        print(f"  - 기준연도: {year}")

        sql = """
            SELECT
                a.seq_no AS sqno,
                a.biz_name,
                b.biz_manager,
                d.가입기한,
                REPLACE(d.가맹일자, '1900-01-01', '') AS 가맹일자,
                e.가산세사유,
                e.거래일자,
                e.대상금액
            FROM mem_user a
            LEFT OUTER JOIN mem_deal b ON a.seq_no = b.seq_no
            LEFT OUTER JOIN mem_admin c ON b.biz_manager = c.admin_id
            LEFT OUTER JOIN 현금영수증가맹점가입의무현황 d ON d.seq_no = a.seq_no
            LEFT OUTER JOIN 가산세내역 e ON e.seq_no = a.seq_no
            WHERE a.seq_no = b.seq_no
                AND a.Del_YN <> 'Y'
                AND b.biz_manager = c.admin_id
                AND a.duzon_ID <> ''
                AND b.keeping_YN = 'Y'
                AND b.kijang_YN = 'Y'
                AND a.biz_type > 3
                AND b.manage_YN = 'Y'
                AND d.가입의무대상 = '대상'
                AND d.기준연도 = %s
                AND (d.가맹일자 = '1900-01-01' OR YEAR(d.가맹일자) = %s OR e.가산세사유 IS NOT NULL)
        """

        params = [year, year]

        if admin_id != 'AAAAA':
            sql += " AND c.admin_name = %s"
            params.append(admin_id)

        if 담당자:
            sql += " AND b.biz_manager = %s"
            params.append(담당자)

        sql += " AND b.biz_manager NOT IN ('환급1','종소세','종소세1','종소세2','종소세3') ORDER BY b.biz_manager"

        print(f"\n🔍 SQL 쿼리:")
        print(f"  Params: {params}")
        print(f"  Query Preview: {sql[:200]}...")

        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            rows = cursor.fetchall()

        print(f"\n✅ 쿼리 실행 성공!")
        print(f"  - 조회된 행 수: {len(rows)}")

        result = []
        for row in rows:
            미가맹사유 = row[5] if row[5] else ''
            if not 미가맹사유 and row[3] and row[4] and row[3] < row[4]:
                미가맹사유 = '미가맹'

            result.append([
                row[0],  # sqno
                row[2],  # biz_manager
                row[1],  # biz_name
                row[3] if row[3] else '',  # 가입기한
                row[4] if row[4] else '',  # 가맹일자
                미가맹사유,  # 사유
                row[6] if row[6] else '',  # 거래일자
                row[7] if row[7] else 0   # 대상금액
            ])

        print(f"  - 결과 데이터 샘플: {result[:2] if result else '데이터 없음'}")
        print(f"\n✅ 응답 성공 (200 OK)")
        print("="*80 + "\n")

        return JsonResponse({
            'success': True,
            'data': result,
            'count': len(result)
        })

    except Exception as e:
        import traceback
        print(f"\n❌ 에러 발생!")
        print(f"  에러 메시지: {str(e)}")
        print(f"\n상세 스택 트레이스:")
        print(traceback.format_exc())
        print("="*80 + "\n")

        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required(login_url="/login/")
def get_vat_data(request):
    """
    3. 부가가치세 신고 현황 (상세)
    """
    print("\n" + "="*80)
    print("[부가가치세 API] 요청 시작")
    print("="*80)

    try:
        담당자 = request.GET.get('staff', None)
        year = int(request.GET.get('year', datetime.datetime.now().year))
        admin_id = request.user.username

        today = datetime.date.today()
        current_month = today.month

        print(f"📥 요청 파라미터:")
        print(f"  - admin_id: {admin_id}")
        print(f"  - 담당자 필터: {담당자 or '전체'}")
        print(f"  - 기준연도: {year}")
        print(f"  - 오늘 날짜: {today}, 현재 월: {current_month}")

        # 현재 작업해야 할 분기/기수 판단
        work_vat = False
        work_qt = 0

        # 부가세 신고 기간 체크 (15일~28일)
        if (current_month in [1, 4, 7, 10] and 15 <= today.day <= 28):
            work_vat = True
            if current_month == 1:
                work_qt = 4
            elif current_month == 4:
                work_qt = 1
            elif current_month == 7:
                work_qt = 2
            elif current_month == 10:
                work_qt = 3

        print(f"  - 부가세 신고 기간 여부: {work_vat}, 분기: {work_qt}")

        if not work_vat:
            print(f"⚠️  현재는 부가세 신고 기간이 아닙니다.")
            print("="*80 + "\n")
            return JsonResponse({
                'success': True,
                'data': [],
                'count': 0,
                'message': '현재는 부가세 신고 기간이 아닙니다.'
            })

        # 과세기간 및 신고구분 설정
        if work_qt == 1:
            kwasekikan = f'{year}년 1기'
            ks2 = '예정(정기)'
            SKGB = 'C17'
        elif work_qt == 2:
            kwasekikan = f'{year}년 1기'
            ks2 = '확정(정기)'
            SKGB = 'C07'
        elif work_qt == 3:
            kwasekikan = f'{year}년 2기'
            ks2 = '예정(정기)'
            SKGB = 'C17'
        else:  # work_qt == 4
            kwasekikan = f'{year}년 2기'
            ks2 = '확정(정기)'
            SKGB = 'C07'

        # 업체 유형별 조건
        if work_qt in [1, 3]:
            biz_type_condition = "a.biz_type = '1'"
        elif work_qt == 2:
            biz_type_condition = "a.biz_type < '5'"
        else:  # work_qt == 4
            biz_type_condition = "a.biz_type < '6'"

        sql = f"""
            SELECT
                a.biz_name,
                a.seq_no AS sqno,
                a.ceo_name,
                a.biz_tel,
                a.biz_no,
                b.biz_manager,
                a.biz_type,
                ISNULL(E.차감납부할세액, 0) AS YN_18,
                ISNULL(E.신고시각, '') AS YN_19,
                ISNULL(E.제출자, '') AS submitter
            FROM mem_user a
            LEFT OUTER JOIN mem_deal b ON a.seq_no = b.seq_no
            LEFT OUTER JOIN mem_admin c ON b.biz_manager = c.admin_id
            LEFT OUTER JOIN 부가가치세전자신고3 E ON E.사업자등록번호 = A.BIZ_NO
                AND E.과세기간 = '{kwasekikan}'
                AND E.과세유형 = '{SKGB}'
            WHERE a.seq_no = b.seq_no
                AND a.duzon_ID <> ''
                AND b.keeping_YN = 'Y'
                AND {biz_type_condition}
                AND a.Del_YN <> 'Y'
                AND b.biz_manager = c.admin_id
        """

        params = []

        if admin_id != 'AAAAA':
            sql += " AND c.admin_name = %s"
            params.append(admin_id)

        if 담당자:
            sql += " AND b.biz_manager = %s"
            params.append(담당자)

        sql += " AND b.biz_manager NOT IN ('환급1','종소세','종소세1','종소세2','종소세3') ORDER BY b.biz_manager"

        print(f"\n🔍 SQL 쿼리:")
        print(f"  과세기간: {kwasekikan}, 신고구분: {ks2}")
        print(f"  Params: {params}")
        print(f"  Query Preview: {sql[:250]}...")

        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            rows = cursor.fetchall()

        print(f"\n✅ 쿼리 실행 성공!")
        print(f"  - 조회된 행 수: {len(rows)}")

        result = []
        idx = 0
        for row in rows:
            # 메일/카톡 이미지 처리 (실제로는 별도 쿼리 필요)
            mailGrade = ''  # TODO: 메일/카톡 조회 추가

            # 신고시각 확인
            isIssue = '✓' if row[8] else ''

            result.append([
                idx,
                row[1],  # sqno
                row[5],  # biz_manager
                row[0],  # biz_name
                row[6],  # biz_type
                mailGrade,  # 메일/카톡
                '✓' if row[8] else '',  # 통합조회 (신고시각 있으면)
                '',  # YN_15 (TODO)
                int(row[7]) if row[7] else 0,  # 납부세액
                '',  # YN_10 (결재) (TODO)
                '',  # YN_13 (TODO)
                isIssue,  # 신고완료 여부
                '',  # inspect_issue (TODO)
                '',  # inspect_elec (TODO)
                ''   # inspect_issue_Txt (TODO)
            ])
            idx += 1

        print(f"  - 결과 데이터 샘플: {result[:2] if result else '데이터 없음'}")
        print(f"\n✅ 응답 성공 (200 OK)")
        print("="*80 + "\n")

        return JsonResponse({
            'success': True,
            'data': result,
            'count': len(result),
            'period': kwasekikan,
            'type': ks2
        })

    except Exception as e:
        import traceback
        print(f"\n❌ 에러 발생!")
        print(f"  에러 메시지: {str(e)}")
        print(f"\n상세 스택 트레이스:")
        print(traceback.format_exc())
        print("="*80 + "\n")

        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required(login_url="/login/")
def get_report_data(request):
    """
    4. 기장보고서 작성 현황 (분기별)
    """
    print("\n" + "="*80)
    print("[기장보고서 API] 요청 시작")
    print("="*80)

    try:
        담당자 = request.GET.get('staff', None)
        admin_id = request.user.username

        today = datetime.date.today()
        current_year = today.year
        current_month = today.month
        current_quarter = (current_month - 1) // 3 + 1

        print(f"📥 요청 파라미터:")
        print(f"  - admin_id: {admin_id}")
        print(f"  - 담당자 필터: {담당자 or '전체'}")
        print(f"  - 현재 연도: {current_year}, 현재 분기: {current_quarter}")

        result = []
        idx = 0

        # 이전 4개 분기 체크
        print(f"\n🔍 이전 4개 분기 조회 시작...")
        for i in range(1, 5):
            quarter = current_quarter - i
            year = current_year

            if quarter <= 0:
                quarter += 4
                year -= 1

            # 1, 3분기는 법인만 체크
            if quarter in [1, 3]:
                biz_type_condition = "a.biz_type IN ('1', '2', '3')"
            else:
                biz_type_condition = "1=1"

            sql = f"""
                SELECT
                    a.seq_no AS sqno,
                    b.biz_manager,
                    a.biz_name,
                    a.biz_type
                FROM mem_user a
                LEFT OUTER JOIN mem_deal b ON a.seq_no = b.seq_no
                LEFT OUTER JOIN mem_admin c ON b.biz_manager = c.admin_id
                WHERE a.seq_no = b.seq_no
                    AND b.biz_manager = c.admin_id
                    AND c.manage_YN = 'Y'
                    AND a.duzon_ID <> ''
                    AND b.keeping_YN = 'Y'
                    AND {biz_type_condition}
                    AND a.Del_YN <> 'Y'
                    AND b.manage_YN = 'Y'
                    AND NOT EXISTS (
                        SELECT 1 FROM Tbl_OFST_KAKAO_SMS
                        WHERE seq_user = a.seq_no
                            AND send_result = 'Y'
                            AND LEFT(send_dt, 4) = '{year}'
                            AND contents LIKE '%{year}년 {quarter}분기 재무제표 및 예상세액 등에 대한 기장현황보고서%'
                    )
            """

            params = []

            if admin_id != 'AAAAA':
                sql += " AND c.admin_name = %s"
                params.append(admin_id)

            if 담당자:
                sql += " AND b.biz_manager = %s"
                params.append(담당자)

            sql += " ORDER BY b.biz_manager"

            print(f"  [{i}/4] {year}년 {quarter}분기 조회 (Params: {params})")

            with connection.cursor() as cursor:
                cursor.execute(sql, params)
                rows = cursor.fetchall()

            print(f"       -> 조회 결과: {len(rows)}건")

            for row in rows:
                # 마감일 계산
                due_day = 25 if row[3] and int(row[3]) <= 3 else 15

                if quarter == 1:
                    due_date = f"{year}년 6월 {due_day}일"
                elif quarter == 2:
                    due_date = f"{year}년 8월 {due_day}일"
                elif quarter == 3:
                    due_date = f"{year}년 11월 {due_day}일"
                else:  # quarter == 4
                    due_date = f"{year + 1}년 2월 {due_day}일"

                # 파일 존재 여부 확인 (TODO: 실제 파일 시스템 체크)
                # 현재는 카카오 발송 여부로만 체크

                result.append([
                    idx,
                    row[1],  # biz_manager
                    row[2],  # biz_name
                    str(year),
                    f'{quarter}분기',
                    due_date,
                    '',  # isXlsExist (파일 존재 여부)
                    i  # priority (1이 가장 급함)
                ])
                idx += 1

        print(f"\n✅ 전체 조회 완료!")
        print(f"  - 총 결과 수: {len(result)}")
        print(f"  - 결과 데이터 샘플: {result[:2] if result else '데이터 없음'}")
        print(f"\n✅ 응답 성공 (200 OK)")
        print("="*80 + "\n")

        return JsonResponse({
            'success': True,
            'data': result,
            'count': len(result)
        })

    except Exception as e:
        import traceback
        print(f"\n❌ 에러 발생!")
        print(f"  에러 메시지: {str(e)}")
        print(f"\n상세 스택 트레이스:")
        print(traceback.format_exc())
        print("="*80 + "\n")

        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required(login_url="/login/")
def get_kani_mm_data(request):
    """
    5. 간이지급명세서(매월) - 사업/일용소득
    """
    print("\n" + "="*80)
    print("[간이지급명세서(매월) API] 요청 시작")
    print("="*80)

    try:
        담당자 = request.GET.get('staff', None)
        admin_id = request.user.username

        # 최근 6개월 데이터 조회
        today = datetime.date.today()
        start_month = today - timedelta(days=150)  # 약 5개월

        print(f"📥 요청 파라미터:")
        print(f"  - admin_id: {admin_id}")
        print(f"  - 담당자 필터: {담당자 or '전체'}")
        print(f"  - 조회 기간: 최근 5개월")

        sql = """
            SELECT
                AA.작업연도,
                (SELECT a.seq_no FROM mem_user a, mem_deal b
                 WHERE a.biz_no = AA.사업자등록번호 AND a.seq_no = b.seq_no) AS sqno,
                (SELECT biz_manager FROM mem_user a, mem_deal b
                 WHERE a.biz_no = AA.사업자등록번호 AND a.seq_no = b.seq_no) AS biz_manager,
                (SELECT biz_name FROM mem_user a, mem_deal b
                 WHERE a.biz_no = AA.사업자등록번호 AND a.seq_no = b.seq_no) AS biz_name,
                SUM(AA.원천사업) AS 원천사업,
                SUM(AA.간이사업) AS 간이사업,
                SUM(AA.원천일용) AS 원천일용,
                SUM(AA.간이일용) AS 간이일용,
                AA.사유
            FROM (
                -- 사업소득 누락분
                SELECT
                    RTRIM(a.지급연월) AS 작업연도,
                    a.사업자등록번호,
                    A.A30 AS 원천사업,
                    ISNULL(B.제출금액, 0) AS 간이사업,
                    0 AS 원천일용,
                    0 AS 간이일용,
                    ISNULL((SELECT TXT_BIGO FROM tbl_kani_v e
                            WHERE e.SEQ_NO IN (SELECT SEQ_NO FROM mem_user WHERE biz_no = a.사업자등록번호)
                              AND e.work_yy >= '2024'
                              AND e.work_yy = LEFT(a.과세연월, 4)
                              AND e.work_banki = RIGHT(a.지급연월, 2)), '') AS 사유
                FROM 원천세전자신고 a WITH (NOLOCK)
                LEFT OUTER JOIN 지급조서간이소득 b WITH (NOLOCK)
                    ON a.사업자등록번호 = b.사업자번호
                    AND b.신고서종류 = '간이지급명세서(거주자의 사업소득)'
                    AND RTRIM(a.지급연월) = RTRIM(REPLACE(b.과세년도, '-', ''))
                WHERE a.과세연월 BETWEEN FORMAT(DATEADD(MONTH, -5, GETDATE()), 'yyyyMM')
                      AND FORMAT(GETDATE(), 'yyyyMM')
                    AND ISNULL(b.사업자번호, '') = ''
                    AND A30 <> 0

                UNION ALL

                -- 사업소득 금액차이분
                SELECT
                    RTRIM(a.지급연월) AS 작업연도,
                    a.사업자등록번호,
                    A.A30 AS 원천사업,
                    ISNULL(B.제출금액, 0) AS 간이사업,
                    0 AS 원천일용,
                    0 AS 간이일용,
                    ISNULL((SELECT TXT_BIGO FROM tbl_kani_v e
                            WHERE e.SEQ_NO IN (SELECT SEQ_NO FROM mem_user WHERE biz_no = a.사업자등록번호)
                              AND e.work_yy >= '2024'
                              AND e.work_yy = LEFT(a.과세연월, 4)
                              AND e.work_banki = RIGHT(a.지급연월, 2)), '') AS 사유
                FROM 원천세전자신고 a WITH (NOLOCK),
                     지급조서간이소득 b WITH (NOLOCK),
                     MEM_DEAL C WITH (NOLOCK),
                     MEM_USER d WITH (NOLOCK)
                WHERE a.과세연월 BETWEEN FORMAT(DATEADD(MONTH, -5, GETDATE()), 'yyyyMM')
                      AND FORMAT(GETDATE(), 'yyyyMM')
                    AND A30 <> 0
                    AND a.사업자등록번호 = b.사업자번호
                    AND b.신고서종류 = '간이지급명세서(거주자의 사업소득)'
                    AND RTRIM(a.지급연월) = RTRIM(REPLACE(b.과세년도, '-', ''))
                    AND A.A30 <> ISNULL(B.제출금액, 0)
                    AND A.사업자등록번호 = d.BIZ_NO
                    AND d.seq_no = c.seq_no
                    AND c.GOYOUNG_BANKI <> 'Y'

                UNION ALL

                -- 일용직 누락분
                SELECT
                    RTRIM(a.지급연월) AS 작업연도,
                    a.사업자등록번호,
                    0 AS 원천사업,
                    0 AS 간이사업,
                    A.A03 AS 원천일용,
                    ISNULL(B.제출금액, 0) AS 간이일용,
                    ISNULL((SELECT TXT_BIGO FROM tbl_kani_v e
                            WHERE e.SEQ_NO IN (SELECT SEQ_NO FROM mem_user WHERE biz_no = a.사업자등록번호)
                              AND e.work_yy >= '2024'
                              AND e.work_yy = LEFT(a.과세연월, 4)
                              AND e.work_banki = RIGHT(a.지급연월, 2)), '') AS 사유
                FROM 원천세전자신고 a WITH (NOLOCK)
                LEFT OUTER JOIN 지급조서간이소득 b WITH (NOLOCK)
                    ON a.사업자등록번호 = b.사업자번호
                    AND b.신고서종류 = '일용근로소득 지급명세서'
                    AND RTRIM(a.지급연월) = RTRIM(REPLACE(b.과세년도, '-', ''))
                WHERE a.과세연월 BETWEEN FORMAT(DATEADD(MONTH, -5, GETDATE()), 'yyyyMM')
                      AND FORMAT(GETDATE(), 'yyyyMM')
                    AND ISNULL(b.사업자번호, '') = ''
                    AND A03 <> 0

                UNION ALL

                -- 일용직 금액차이분
                SELECT
                    RTRIM(a.지급연월) AS 작업연도,
                    a.사업자등록번호,
                    0 AS 원천사업,
                    0 AS 간이사업,
                    A.A03 AS 원천일용,
                    ISNULL(B.제출금액, 0) AS 간이일용,
                    ISNULL((SELECT TXT_BIGO FROM tbl_kani_v e
                            WHERE e.SEQ_NO IN (SELECT SEQ_NO FROM mem_user WHERE biz_no = a.사업자등록번호)
                              AND e.work_yy >= '2024'
                              AND e.work_yy = LEFT(a.과세연월, 4)
                              AND e.work_banki = RIGHT(a.지급연월, 2)), '') AS 사유
                FROM 원천세전자신고 a WITH (NOLOCK),
                     지급조서간이소득 b WITH (NOLOCK),
                     MEM_DEAL C WITH (NOLOCK),
                     MEM_USER d WITH (NOLOCK)
                WHERE a.과세연월 BETWEEN FORMAT(DATEADD(MONTH, -5, GETDATE()), 'yyyyMM')
                      AND FORMAT(GETDATE(), 'yyyyMM')
                    AND A03 <> 0
                    AND a.사업자등록번호 = b.사업자번호
                    AND b.신고서종류 = '일용근로소득 지급명세서'
                    AND RTRIM(a.지급연월) = RTRIM(REPLACE(b.과세년도, '-', ''))
                    AND A.A03 <> ISNULL(B.제출금액, 0)
                    AND A.사업자등록번호 = d.BIZ_NO
                    AND d.seq_no = c.seq_no
                    AND c.GOYOUNG_BANKI <> 'Y'
            ) AA
        """

        params = []

        if admin_id != 'AAAAA':
            sql += """
                WHERE (SELECT biz_manager FROM mem_user a, mem_deal b
                       WHERE a.biz_no = AA.사업자등록번호 AND a.seq_no = b.seq_no)
                IN (SELECT Admin_id FROM mem_admin
                    WHERE admin_name = %s AND admin_id <> %s)
            """
            params.extend([admin_id, admin_id])

        sql += " GROUP BY AA.작업연도, AA.사업자등록번호, AA.사유 ORDER BY 1, 2"

        print(f"\n🔍 SQL 쿼리:")
        print(f"  Params: {params}")
        print(f"  Query Type: 복잡한 UNION ALL 쿼리 (사업/일용소득 누락분 + 차이분)")

        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            rows = cursor.fetchall()

        print(f"\n✅ 쿼리 실행 성공!")
        print(f"  - 조회된 행 수: {len(rows)}")

        result = []
        idx = 0
        for row in rows:
            if row[1] and row[2] and row[3]:  # sqno, biz_manager, biz_name이 있는 경우만
                작업연월 = row[0]
                년도 = 작업연월[:4]
                월 = 작업연월[4:6]

                result.append([
                    idx,
                    row[1],  # sqno
                    row[2],  # biz_manager
                    row[3],  # biz_name
                    년도,
                    월,
                    int(row[6]) if row[6] else 0,  # 원천일용
                    int(row[7]) if row[7] else 0,  # 간이일용
                    int(row[4]) if row[4] else 0,  # 원천사업
                    int(row[5]) if row[5] else 0,  # 간이사업
                    row[8] if row[8] else ''  # 사유
                ])
                idx += 1

        print(f"  - 필터링 후 결과 수: {len(result)}")
        print(f"  - 결과 데이터 샘플: {result[:2] if result else '데이터 없음'}")
        print(f"\n✅ 응답 성공 (200 OK)")
        print("="*80 + "\n")

        return JsonResponse({
            'success': True,
            'data': result,
            'count': len(result)
        })

    except Exception as e:
        import traceback
        print(f"\n❌ 에러 발생!")
        print(f"  에러 메시지: {str(e)}")
        print(f"\n상세 스택 트레이스:")
        print(traceback.format_exc())
        print("="*80 + "\n")

        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required(login_url="/login/")
def get_kani_banki_data(request):
    """
    6. 간이지급명세서(반기) - 근로소득
    """
    print("\n" + "="*80)
    print("[간이지급명세서(반기) API] 요청 시작")
    print("="*80)

    try:
        담당자 = request.GET.get('staff', None)
        admin_id = request.user.username

        print(f"📥 요청 파라미터:")
        print(f"  - admin_id: {admin_id}")
        print(f"  - 담당자 필터: {담당자 or '전체'}")

        sql = """
            SELECT A.담당, A.사업자번호, MAX(A.상호) AS 상호, A.년도, A.구분,
                   SUM(A.지급총액) AS 지급총액, SUM(A.지급조서) AS 지급조서,
                   SUM(A.지급총액) - SUM(A.지급조서) AS 차이금액, MAX(A.사유) AS 사유
            FROM (
                -- 지급총액(상반기)
                SELECT C.biz_manager AS 담당, B.biz_no AS 사업자번호, B.Biz_Name AS 상호,
                       A.work_yy AS 년도, '상반기' AS 구분,
                       SUM(A.지급총액 - A.식대 - A.자가운전보조금 - A.육아수당 - A.연구개발수당 - A.기타수당1) AS 지급총액,
                       0 AS 지급조서, '' AS 사유
                FROM 급여지급현황 A
                JOIN mem_user B ON A.seq_no = B.seq_no
                JOIN mem_deal C ON B.seq_no = C.seq_no
                WHERE A.work_yy >= '2024' AND A.work_mm <= 6
                GROUP BY C.biz_manager, B.biz_no, B.Biz_Name, A.work_yy

                UNION ALL

                -- 지급총액(하반기)
                SELECT C.biz_manager, B.biz_no, B.Biz_Name, A.work_yy, '하반기',
                       SUM(A.지급총액 - A.식대 - A.자가운전보조금 - A.육아수당 - A.연구개발수당 - A.기타수당1),
                       0, ''
                FROM 급여지급현황 A
                JOIN mem_user B ON A.seq_no = B.seq_no
                JOIN mem_deal C ON B.seq_no = C.seq_no
                WHERE A.work_yy >= '2024' AND A.work_mm > 6
                GROUP BY C.biz_manager, B.biz_no, B.Biz_Name, A.work_yy

                UNION ALL

                -- 지급조서(상반기)
                SELECT C.biz_manager, A.사업자번호, A.상호, LEFT(A.과세년도, 4), '상반기', 0,
                       SUM(제출금액),
                       ISNULL((SELECT TOP 1 TXT_BIGO FROM tbl_kani E
                               WHERE E.SEQ_NO IN (SELECT seq_no FROM mem_user WHERE biz_no = A.사업자번호)
                                 AND E.work_yy = LEFT(A.과세년도, 4) AND E.work_banki = 'Jan'), '')
                FROM 지급조서간이소득 A
                JOIN mem_user B ON A.사업자번호 = B.biz_no
                JOIN mem_deal C ON B.seq_no = C.seq_no
                WHERE A.신고서종류 = '간이지급명세서(근로소득)'
                  AND LEFT(A.과세년도, 4) IN ('2024', '2025', '2026')
                GROUP BY A.사업자번호, A.상호, LEFT(A.과세년도, 4), C.biz_manager

                UNION ALL

                -- 지급조서(하반기)
                SELECT C.biz_manager, A.사업자번호, A.상호, LEFT(A.과세년도, 4), '하반기', 0,
                       SUM(제출금액),
                       ISNULL((SELECT TOP 1 TXT_BIGO FROM tbl_kani E
                               WHERE E.SEQ_NO IN (SELECT seq_no FROM mem_user WHERE biz_no = A.사업자번호)
                                 AND E.work_yy = LEFT(A.과세년도, 4) AND E.work_banki = 'Jan'), '')
                FROM 지급조서간이소득 A
                JOIN mem_user B ON A.사업자번호 = B.biz_no
                JOIN mem_deal C ON B.seq_no = C.seq_no
                WHERE A.신고서종류 = '간이지급명세서(근로소득)'
                  AND LEFT(A.과세년도, 4) IN ('2024', '2025', '2026')
                GROUP BY A.사업자번호, A.상호, LEFT(A.과세년도, 4), C.biz_manager
            ) A
        """

        params = []

        if admin_id != 'AAAAA':
            sql += """
                WHERE EXISTS (SELECT 1 FROM mem_user E
                              JOIN mem_deal F ON E.seq_no = F.seq_no
                              WHERE E.biz_no = A.사업자번호
                                AND F.biz_manager IN (SELECT admin_id FROM mem_admin
                                                      WHERE admin_name = %s AND admin_id <> %s))
            """
            params.extend([admin_id, admin_id])

        sql += """
            GROUP BY A.담당, A.사업자번호, A.년도, A.구분
            HAVING SUM(A.지급총액) - SUM(A.지급조서) <> 0
            ORDER BY A.년도, A.담당, A.사업자번호, A.구분
        """

        print(f"\n🔍 SQL 쿼리:")
        print(f"  Params: {params}")
        print(f"  Query Type: 복잡한 UNION ALL 쿼리 (급여지급현황 + 지급조서)")

        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            rows = cursor.fetchall()

        print(f"\n✅ 쿼리 실행 성공!")
        print(f"  - 조회된 행 수: {len(rows)}")

        result = []
        idx = 0
        today = datetime.date.today()
        current_month = today.month

        print(f"  - 현재 월: {current_month} (필터링 적용)")

        for row in rows:
            # 현재 월에 따라 표시할 데이터 필터링
            if current_month >= 7 and current_month <= 12:
                if row[4] != '상반기':  # 하반기는 제외
                    continue

            result.append([
                idx,
                row[0],  # 담당
                row[2],  # 상호
                row[3],  # 년도
                row[4],  # 구분
                int(row[5]) if row[5] else 0,  # 지급총액
                int(row[6]) if row[6] else 0,  # 지급조서
                int(row[7]) if row[7] else 0,  # 차이금액
                row[8] if row[8] else ''  # 사유
            ])
            idx += 1

        print(f"  - 필터링 후 결과 수: {len(result)}")
        print(f"  - 결과 데이터 샘플: {result[:2] if result else '데이터 없음'}")
        print(f"\n✅ 응답 성공 (200 OK)")
        print("="*80 + "\n")

        return JsonResponse({
            'success': True,
            'data': result,
            'count': len(result)
        })

    except Exception as e:
        import traceback
        print(f"\n❌ 에러 발생!")
        print(f"  에러 메시지: {str(e)}")
        print(f"\n상세 스택 트레이스:")
        print(traceback.format_exc())
        print("="*80 + "\n")

        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
