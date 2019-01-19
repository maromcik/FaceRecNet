from django.http.response import JsonResponse, HttpResponse, HttpResponseRedirect
from django.views.decorators.http import require_GET, require_POST
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.conf import settings
from webpush import send_user_notification
from LiveView import views
from LiveView.models import Setting

current_user = None


@require_GET
def home(request):
    webpush_settings = getattr(settings, 'WEBPUSH_SETTINGS', {})
    vapid_key = webpush_settings.get('VAPID_PUBLIC_KEY')
    user = request.user
    try:
        running = views.rec_threads.facerecognition_thread.isAlive()
    except AttributeError:
        running = False
    subscription = Setting.objects.get(pk=1).subscription
    return render(request, 'home.html', {user: user, 'vapid_key': vapid_key, 'running': running, 'subscription': subscription})

def subscribe(request):
    user = request.user
    global current_user
    current_user = user
    if user.is_authenticated:
        subscription = True
    else:
        subscription = False
    try:
        running = views.rec_threads.facerecognition_thread.isAlive()
    except AttributeError:
        running = False
    setting = Setting.objects.get(id=1)
    setting.subscription = subscription
    setting.save()
    return render(request, 'home.html', {user: user, 'subscription': subscription, 'running': running})

def unsubscribe(request):
    user = request.user
    subscription = False
    global current_user
    current_user = None
    try:
        running = views.rec_threads.facerecognition_thread.isAlive()
    except AttributeError:
        running = False
    setting = Setting.objects.get(id=1)
    setting.subscription = subscription
    setting.save()
    return render(request, 'home.html', {user: user, 'subscription': subscription,'running': running})


def notifikacia(request):
    if current_user is not None:
        user = current_user
        payload = {'head': 'ring', 'body': 'someone is ringing'}
        try:
            send_user_notification(user=user, payload=payload, ttl=1000)
            print("sent")
        except TypeError:
            print("push unsuccessful, much like you")
    else:
        print("no user")
    return HttpResponseRedirect('../')
