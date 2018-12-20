from django.urls import path
from . import views

app_name = 'LiveView'
urlpatterns = [
    path('', views.index, name='index'),
    path('login', views.login, name='login'),
    path('run', views.runfacerec, name='run'),
]