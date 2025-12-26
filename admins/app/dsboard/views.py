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
