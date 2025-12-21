from django import forms
from django.forms import ModelForm

from app.models import MemUser, userProfile

class MemUserForm(forms.ModelForm):
    class Meta:
        model = MemUser
        fields = [
            'seq_no', 'duzon_id', 'user_id', 'user_pwd', 'name', 'ssn', 'email', 
            'zipcode', 'addr1', 'addr2', 'tel_no', 'hp_no', 'taxation_no', 'biz_image', 
            'taxoffice_code', 'taxbank_acc', 'ward_off', 'biz_par_chk', 'biz_par_ms', 
            'biz_par_rate', 'biz_par_ssn', 'biz_type', 'upjong', 'biz_no', 'biz_name', 
            'ceo_name', 'uptae', 'jongmok', 'biz_zipcode', 'biz_addr1', 'biz_addr2', 
            'biz_tel', 'biz_fax', 'isrnd', 'saletimail', 'saletiname', 'isventure', 
            'biz_start_day', 'biz_end_day', 'biz_end_reason', 'ret_bank_code', 
            'ret_bank_name', 'ret_account', 'reg_date', 'up_date', 'log_date', 
            'dk_manage', 'del_yn', 'del_date', 'del_reason', 'pay_month', 'pay_year', 
            'pay_not', 'sale_confirm', 'etc', 'open_date', 'close_date', 'close_resn', 
            'join_yn', 'uptaecd', 'biz_area'
        ]

        widgets = {
            'user_pwd': forms.PasswordInput(attrs={'placeholder': '비밀번호를 입력하세요'}),
            'reg_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'up_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'log_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'del_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

        labels = {
            'seq_no': '순번',
            'duzon_id': '더존 ID',
            'user_id': '사용자 ID',
            'user_pwd': '비밀번호',
            'name': '이름',
            'ssn': '주민등록번호',
            'email': '이메일',
            'zipcode': '우편번호',
            'addr1': '주소1',
            'addr2': '주소2',
            'tel_no': '전화번호',
            'hp_no': '휴대폰번호',
            'taxation_no': '세무사 번호',
            'biz_image': '사업자 이미지',
            'taxoffice_code': '세무서 코드',
            'taxbank_acc': '세무 은행 계좌',
            'ward_off': '관리 구역',
            'biz_par_chk': '사업자 파트너 체크',
            'biz_par_ms': '사업자 파트너 MS',
            'biz_par_rate': '파트너 비율',
            'biz_par_ssn': '파트너 주민등록번호',
            'biz_type': '사업 유형',
            'upjong': '업종',
            'biz_no': '사업자 번호',
            'biz_name': '상호명',
            'ceo_name': '대표자명',
            'uptae': '업태',
            'jongmok': '종목',
            'biz_zipcode': '사업장 우편번호',
            'biz_addr1': '사업장 주소1',
            'biz_addr2': '사업장 주소2',
            'biz_tel': '사업장 전화번호',
            'biz_fax': '사업장 팩스번호',
            'isrnd': '연구개발 여부',
            'saletimail': '영업 담당 이메일',
            'saletiname': '영업 담당자명',
            'isventure': '벤처기업 여부',
            'biz_start_day': '사업 시작일',
            'biz_end_day': '사업 종료일',
            'biz_end_reason': '사업 종료 사유',
            'ret_bank_code': '반환 은행 코드',
            'ret_bank_name': '반환 은행명',
            'ret_account': '반환 계좌',
            'reg_date': '등록일',
            'up_date': '수정일',
            'log_date': '로그일',
            'dk_manage': 'DK 관리',
            'del_yn': '삭제 여부',
            'del_date': '삭제일',
            'del_reason': '삭제 사유',
            'pay_month': '월 납부액',
            'pay_year': '연 납부액',
            'pay_not': '미납액',
            'sale_confirm': '매출 확정',
            'etc': '기타',
            'open_date': '개업일',
            'close_date': '폐업일',
            'close_resn': '폐업 사유',
            'join_yn': '가입 여부',
            'uptaecd': '업태 코드',
            'biz_area': '사업 구역',
        }

        help_texts = {
            'user_id': '고유한 사용자 ID를 입력하세요.',
            'email': '연락 가능한 이메일 주소를 입력하세요.',
            'biz_no': '사업자 번호를 입력하세요.',
        }

    def clean_user_id(self):
        user_id = self.cleaned_data.get('user_id')
        if MemUser.objects.filter(user_id=user_id).exists():
            raise forms.ValidationError('이미 사용 중인 사용자 ID입니다.')
        return user_id


class MemberProfileUploadForm(ModelForm):
    class Meta:
        model = userProfile
        fields = ["title", "image", "description"]
