from django.shortcuts import render
from app.models import MemAdmin
from django.core.serializers import serialize
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import json  # Import json to deserialize the serialized data
from django.http import JsonResponse

@login_required(login_url="/login/")
def index(request):
    context = {

    }
    # return render(request, 'admin/staffList_AGgrid2.html', context)
    return render(request, 'admin/staffList2.html')


@csrf_exempt
def mem_admin(request):
    mem_admins = MemAdmin.objects.values('admin_id', 'admin_pwd')
    return JsonResponse(list(mem_admins), safe=False)
