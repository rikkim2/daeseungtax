from django.contrib.auth import authenticate, login
from django.shortcuts import redirect, render
from .forms import LoginForm
from django.contrib.auth.models import User
from app.models import MemAdmin
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.views import LogoutView
from django.shortcuts import redirect

class CustomLogoutView(LogoutView):
    def dispatch(self, request, *args, **kwargs):
        # 세션 삭제
        request.session.flush()
        return super().dispatch(request, *args, **kwargs)


@csrf_exempt
def login_view(request):
    msg = ""
    form = LoginForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            adminName = form.cleaned_data.get("adminName")
            password = form.cleaned_data.get("password")
            try:
                admin = MemAdmin.objects.get(admin_id=adminName)
                if admin is not None:
                    authuser = authenticate(username=adminName, password=password)
                    if authuser is not None :
                        if admin.admin_pwd==password:
                            login(request, authuser)
                            request.session['Admin_Grade'] = admin.grade
                            request.session['Admin_Biz_Level'] = admin.biz_level
                            request.session['Admin_Area'] = admin.admin_biz_area    
                            request.session['Admin_Id'] = admin.admin_id                          
                            return  redirect('dsboard') 
                        else:
                            msg = "비밀번호가 맞지 않습니다."    
                    else:
                        #관리자가 auth_user 테이블에 없는 상태    
                        if admin.admin_id==adminName and admin.admin_pwd==password:  
                            new_user = User.objects.create_user(admin.admin_id,admin.admin_email,admin.admin_pwd)
                            new_user.is_staff = True
                            new_user.save()
                            # MemAdmin 객체의 user_id 필드 업데이트
                            admin.user_id = new_user.id
                            admin.save()

                            authuser = authenticate(username=adminName, password=password)
                            login(request, authuser)
                            request.session['Admin_Grade'] = admin.grade
                            request.session['Admin_Biz_Level'] = admin.biz_level
                            request.session['Admin_Area'] = admin.admin_biz_area    
                            request.session['Admin_Id'] = admin.admin_id                             
                            return  redirect('dsboard')  
                        else:
                            msg = '대소문자를 구분합니다.'                                                      
            except MemAdmin.DoesNotExist:
                msg = '가입되지 않은 담당자입니다.'   
        else:
            msg = '이름과 비밀번호를 입력하세요'  
    return render(request, 'admin/login.html', {'form': form, 'msg': msg})