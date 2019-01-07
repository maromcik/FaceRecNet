from django.http.response import JsonResponse, HttpResponse
from django.views.decorators.http import require_GET, require_POST
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.conf import settings

current_user = None

@require_GET
def home(request):
    webpush_settings = getattr(settings, 'WEBPUSH_SETTINGS', {})
    vapid_key = webpush_settings.get('VAPID_PUBLIC_KEY')
    user = request.user
    return render(request, 'home.html', {user: user, 'vapid_key': vapid_key})

def getUser(sender, user, request, **kwargs):
    global current_user
    current_user = user

def releaseUser(sender, user, request, **kwargs):
    global current_user
    current_user = None

user_logged_in.connect(getUser)
user_logged_out.connect(releaseUser)