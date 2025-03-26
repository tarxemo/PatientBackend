from django.http import JsonResponse
from django.shortcuts import render

from authApp.models import CustomUser

def call(request):
    return render(request, 'call.html')

def get_users(request):
    users = CustomUser.objects.exclude(username=request.user.username).values("id", "username")
    return JsonResponse(list(users), safe=False)