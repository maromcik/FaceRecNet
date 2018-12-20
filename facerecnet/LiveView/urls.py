from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf.urls import url
from . import views

app_name = 'LiveView'
urlpatterns = [
    path('', views.index, name='index'),
    path('run', views.runfacerec, name='run'),
]