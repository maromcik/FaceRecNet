from django.http.response import JsonResponse, HttpResponse
from django.views.decorators.http import require_GET, require_POST
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.conf import settings
from LiveView import views

current_user = None
subscription = False

@require_GET
def home(request):
    webpush_settings = getattr(settings, 'WEBPUSH_SETTINGS', {})
    vapid_key = webpush_settings.get('VAPID_PUBLIC_KEY')
    user = request.user
    try:
        running = views.rec_threads.facerecognition_thread.isAlive()
    except AttributeError:
        running = False
    return render(request, 'home.html', {user: user, 'vapid_key': vapid_key, 'running': running, 'subscription': subscription})

def subscribe(request):
    user = request.user
    global current_user
    current_user = user
    global subscription
    if user.is_authenticated:
        subscription = True
    else:
        subscription = False
    try:
        running = views.rec_threads.facerecognition_thread.isAlive()
    except AttributeError:
        running = False
    return render(request, 'home.html', {user: user, 'subscription': subscription, 'running': running})

def unsubscribe(request):
    user = request.user
    global subscription
    subscription = False
    global current_user
    current_user = None
    try:
        running = views.rec_threads.facerecognition_thread.isAlive()
    except AttributeError:
        running = False
    return render(request, 'home.html', {user: user, 'subscription': subscription,'running': running})