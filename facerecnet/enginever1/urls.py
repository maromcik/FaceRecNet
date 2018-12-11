from django.urls import path
from . import views

app_name = 'enginever1'
urlpatterns = [
    path('', views.index, name='index'),
    path('run', views.runfacerec, name='run'),
]