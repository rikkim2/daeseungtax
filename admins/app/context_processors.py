import datetime
from app.models import MemAdmin, userProfile

def common_context(request):
    context = {}
    if request.session.get('Admin_Id'):  # 세션에 Admin_Id가 있을 경우만 처리
        try:
            mem_admin = MemAdmin.objects.get(admin_id=request.session.get('Admin_Id'))
            context['memadmin'] = mem_admin
            
            userprofile = userProfile.objects.filter(title=mem_admin.seq_no)
            if userprofile.exists():
                userprofile = userprofile.latest('description')
                context['userProfile'] = userprofile
            
            context['dateNow'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        except MemAdmin.DoesNotExist:
            # 관리자 정보가 없는 경우 처리
            context['memadmin'] = None
        except Exception as e:
            # 기타 예외 처리
            context['error'] = str(e)
    return context
