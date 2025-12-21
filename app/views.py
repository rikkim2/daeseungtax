
from django import template
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.template import loader
from django.urls import reverse
from app.models import MemUser

# 지우기...
def landing(request):
    context = {}
    return  render(request, "landing.html",context)

def chartfloat(request):
    context = {}
    return  render(request, "chart-flot.html",context)
@login_required(login_url="/login/")
def dashboard(request):

    # 좌측메뉴 활성화표시
    #context = {'segment': 'index.html'}
    context = {}
    #context['active_menu'] = 'profile'
    memuser = MemUser.objects.get(user_id=request.user.username)
    context['memuser'] = memuser

    return render(request, "dashboard.html",context)



@login_required(login_url="/login/")
def pages(request):
    context = {}
    # All resource paths end in .html.
    # Pick out the html file name from the url. And load that template.
    memuser = MemUser.objects.get(user_id=request.user.username)
    context['memuser'] = memuser
 
    try:
        load_template = request.path.split('/')[-1]

        if load_template == 'admin':
            return HttpResponseRedirect(reverse('admin:index'))

            
        segment, active_menu = get_segment( request )
        
        context['segment']     = segment
        context['active_menu'] = active_menu
        
        html_template = loader.get_template(load_template+'.html')
        return HttpResponse(html_template.render(context, request))

    except template.TemplateDoesNotExist:
        html_template = loader.get_template('error404.html')
        return HttpResponse(html_template.render(context, request))

    except:
        html_template = loader.get_template('error500.html')
        return HttpResponse(html_template.render(context, request))


# Helper - Extract current page name from request 
def get_segment( request ): 

    try:

        segment     = request.path.split('/')[-1]
        active_menu = None

        if segment == '':
            segment     = 'index'
            active_menu = 'dashboard'

        if segment.startswith('dashboards-'):
            active_menu = 'dashboard'

        if segment.startswith('account-') or segment.startswith('users-') or segment.startswith('profile-') or segment.startswith('projects-') or segment.startswith('virtual-'):
            active_menu = 'pages'

        if  segment.startswith('notifications') or segment.startswith('sweet-alerts') or segment.startswith('charts.html') or segment.startswith('widgets') or segment.startswith('pricing'):
            active_menu = 'pages'

        if  segment.startswith('applications'):    
            active_menu = 'apps'

        return segment, active_menu     

    except:
        return 'index', 'dashboard'


