from django.urls import path, include

from . import views


app_name = 'LiveView'
urlpatterns = [
    path('', views.index, name='index'),
    path('stream', views.stream, name='stream'),
    path('encoding', views.run_encodings, name='Run Encodings'),
    path('load', views.load_files, name='Load Files'),
    path('grab', views.grab_cap, name='Grab Capture'),
]
