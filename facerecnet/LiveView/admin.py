from django.contrib import admin

from .models import Person, Log

admin.site.register(Person)
admin.site.register(Log)