from django.contrib import admin
from LiveView.models import Person, Log
from django.utils.html import format_html


class LogAdmin(admin.ModelAdmin):
    list_display = ['person', 'time', 'granted', 'snapshot']
    list_filter = ['person', 'time', 'granted']
    search_fields = ['person__name']




class PersonAdmin(admin.ModelAdmin):

    list_filter = ['name', 'authorized']
    search_fields = ['name']

    def image_tag(self, obj):
        return format_html('<img src="{}" />'.format(obj.file.url))


    image_tag.short_description = 'Image'

    list_display = ['name', 'authorized', 'file', 'image_tag',]

admin.site.register(Person, PersonAdmin)
admin.site.register(Log, LogAdmin)
