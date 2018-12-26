from django.contrib import admin
from LiveView.models import Person, Log
from django.utils.safestring import mark_safe
from django.utils.html import format_html


class LogAdmin(admin.ModelAdmin):
    list_display = ['person', 'time', 'granted', 'image_tag']
    list_filter = ['person', 'time', 'granted']
    search_fields = ['person__name']

    def image_tag(self, obj):
        try:
            return mark_safe('<img src="{url}" height={height} />'.format(
                url = obj.snapshot.url,
                height=150,
            )
        )
        except ValueError:
            pass

    image_tag.short_description = 'Image'



class PersonAdmin(admin.ModelAdmin):

    list_filter = ['authorized']
    search_fields = ['name']
    fields = ['name', 'authorized', 'file']
    list_display = ['name', 'authorized', 'image_tag']



    def image_tag(self, obj):
        return mark_safe('<img src="{url}" height={height} />'.format(
            url = obj.file.url,
            height=150,
        )
    )

    image_tag.short_description = 'Image'

admin.site.register(Log, LogAdmin)
admin.site.register(Person, PersonAdmin)

