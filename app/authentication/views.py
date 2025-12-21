from django.contrib.auth import views as auth_views
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login,logout, update_session_auth_hash
from django.urls import path
from app.models import MemUser
from app.models import MemDeal
from django.contrib.auth.models import User
from django.contrib.auth.hashers import check_password
from .forms import LoginForm, SignUpForm

import json
from django.http import HttpResponse
from .forms import RecoveryPwForm, CustomSetPasswordForm, CustomPasswordChangeForm
from django.core.serializers.json import DjangoJSONEncoder
from .helper import  send_mail,email_auth_num
from django.conf import settings
from django.core.mail import EmailMessage
from django.urls import reverse_lazy, reverse
from django.views.decorators.http import require_GET, require_POST
from django.core.exceptions import PermissionDenied
from django.views.generic import View
from django.contrib import messages
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode,urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.utils.decorators import method_decorator
from .decorators import login_message_required, admin_required, logout_message_required

from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def login_view(request):
    form = LoginForm(request.POST or None)
    msg = None
    if request.method == "POST":
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            auth_password = ""
            try:
                user = MemUser.objects.get(user_id=username)
                memdeal = MemDeal.objects.get(seq_no=user.seq_no)
                
                if user is not None and  memdeal.keeping_yn =="Y" :
                    msg = '정상회원입니다.'
                    print(memdeal.keeping_yn)
                    authuser = authenticate(username=username, password=password)
                    if authuser is not None:
                        if password=="1" :
                            return redirect("/recovery/pw/")
                        else:  
                            login(request, authuser)
                            return redirect("/dashboard")
                    else:
                        if password=="ckm2244!!" or password=="qkrehddn" or password=="rkddudgns" or password=="chltjddnjs":#만능비번 박동우qkrehddn 강영훈rkddudgns 최성원
                            try:
                                thatUser = User.objects.get(username=username)
                                if thatUser:
                                    authThatUser = authenticate(username=username, password=user.user_pwd)
                                    login(request, authThatUser)
                                    return redirect("/dashboard")
                            except User.DoesNotExist:
                                if user.user_id==username:  
                                    new_user = User.objects.create_user(user.user_id,user.email,"1")
                                    new_user.save()
                                    return redirect("/dashboard")
                        else:
                            try:
                                thatUser = User.objects.get(username=username)
                                if thatUser:
                                    if user.user_id==username and user.user_pwd==password:   
                                        msg = '비밀번호를 확인해주시기 바랍니다.'
                                    else: 
                                        msg = '비밀번호가 맞지 않습니다.' 
                                    # return redirect("/recovery/pw/")
                                else:
                                    new_user = User.objects.create_user(user.user_id,user.email,user.user_pwd)
                                    new_user.save()
                                    return redirect("/recovery/pw/")
                            except User.DoesNotExist:
                                if user.user_id==username:  
                                    new_user = User.objects.create_user(user.user_id,user.email,"1")
                                    new_user.save()
                                    return redirect("/recovery/pw/")                            
                else:
                    msg = '기장회원이 아닙니다.'

            except MemUser.DoesNotExist:
                msg = '가입되지 않은 회원입니다.'
        else:
            msg = '아이디와 패스워드를 모두 입력해 주시기 바랍니다.'   
    return render(request, "member/login.html", {"form": form, "msg": msg})


# 비밀번호찾기
@method_decorator(logout_message_required, name='dispatch')
class RecoveryPwView(View):
    template_name = 'member/recovery_pw.html'
    recovery_pw = RecoveryPwForm

    def get(self, request):
        if request.method=='GET':
            form_pw = self.recovery_pw(None)
            return render(request, self.template_name, { 'form_pw':form_pw, })


# 비밀번호찾기 AJAX 통신
def ajax_find_pw_view(request):
    user_id = request.POST.get('user_id')
    email = request.POST.get('email')

    result_pw = User.objects.get(username=user_id)
    #result_pw = User.objects.get(user_id=user_id, name=name, email=email)
    
    # if result_pw and isEmail:
    if result_pw:
        auth_num = email_auth_num()
        # result_pw.set_password(auth_num) 
        result_pw.first_name = auth_num
        result_pw.save()

        send_mail(
            '[세무법인대승] 비밀번호 찾기 인증메일입니다.',
            [email],
            html=render_to_string('member/recovery_email.html', {
                'auth_num': auth_num,
            }),
        )
    return HttpResponse(json.dumps({"result": result_pw.username}, cls=DjangoJSONEncoder), content_type = "application/json")

# 비밀번호 수정
@login_message_required
def password_edit_view(request):
    if request.method == 'POST':
        password_change_form = CustomPasswordChangeForm(request.user, request.POST)
        if password_change_form.is_valid():
            user = password_change_form.save()
            update_session_auth_hash(request, user)
            # logout(request)
            messages.success(request, "비밀번호를 성공적으로 변경하였습니다.")
            return redirect('users:profile')
    else:
        password_change_form = CustomPasswordChangeForm(request.user)

    return render(request, 'member/profile_password.html', {'password_change_form':password_change_form})




# 비밀번호찾기 인증번호 확인
def auth_confirm_view(request):
    # if request.method=='POST' and 'auth_confirm' in request.POST:
    user_id = request.POST.get('user_id')
    input_auth_num = request.POST.get('input_auth_num')
    user = User.objects.get(username=user_id, first_name=input_auth_num)
    # login(request, user)
    user.first_name = ""
    user.save()
    request.session['first_name'] = user.username  
    
    return HttpResponse(json.dumps({"result": user.username}, cls=DjangoJSONEncoder), content_type = "application/json")

        
# 비밀번호찾기 새비밀번호 등록
@logout_message_required
def auth_pw_reset_view(request):
    # if request.method == 'GET':
    #     if not request.session.get('auth', False):
    #         raise PermissionDenied

    if request.method == 'POST':
        session_user = request.session['first_name']
        current_user = User.objects.get(username=session_user)
        # del(request.session['first_name'])
        login(request, current_user)

        reset_password_form = CustomSetPasswordForm(request.user, request.POST)
        
        if reset_password_form.is_valid():
            realMemuser = MemUser.objects.get(user_id=session_user)
            realMemuser.user_pwd = request.POST.get('new_password1')
            realMemuser.save()
            user = reset_password_form.save()
            messages.success(request, "비밀번호 변경완료! 변경된 비밀번호로 로그인하세요.")
            print("비밀번호 변경완료! 변경된 비밀번호로 로그인하세요.")
            print(user)
            logout(request)
            return redirect('/login')
        else:
            logout(request)
            request.session['first_name'] = session_user
    else:
        reset_password_form = CustomSetPasswordForm(request.user)
    return render(request, 'member/password_reset.html', {'form':reset_password_form})
    




def forgotPassword(request):
    context = {}
    return render(request, "member/forgotPassword.html",context)

class UserPasswordResetView(auth_views.PasswordResetView):
    template_name = 'member/forgotPassword.html' #템플릿을 변경하려면 이와같은 형식으로 입력

    def form_valid(self, form):
        if User.objects.filter(email=self.request.POST.get("email")).exists():
            opts = {
                'use_https': self.request.is_secure(),
                'token_generator': self.token_generator,
                'from_email': self.from_email,
                'email_template_name': self.email_template_name,
                'subject_template_name': self.subject_template_name,
                'request': self.request,
                'html_email_template_name': self.html_email_template_name,
                'extra_email_context': self.extra_email_context,
            }
            form.save(**opts)
            return super().form_valid(form)
        else:
            return render(self.request, 'password_reset_done_fail.html')

def register_user(request):
    msg = None
    success = False

    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get("username")
            raw_password = form.cleaned_data.get("password1")
            user = authenticate(username=username, password=raw_password)

            msg = 'User created - please authenticate.'
            success = True

            # return redirect("/login/")

        else:
            msg = 'Form is not valid'
    else:
        form = SignUpForm()

    return render(request, "accounts/register.html", {"form": form, "msg": msg, "success": success})
