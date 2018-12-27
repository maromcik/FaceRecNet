from django.contrib import admin
from LiveView.models import Person, Log
from django.utils.safestring import mark_safe
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.urls import path
from LiveView.views import x
from django.http import HttpResponseRedirect


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
    change_list_template = "LiveView/change_list.html"


    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('encoding/', self.run_encodings),
            path('load/', self.load_files),
        ]
        return my_urls + urls

    @method_decorator(login_required(login_url='/admin/login'))
    def run_encodings(self, request):
        x.load_files()
        x.known_subjects_descriptors()
        x.load_files()
        self.message_user(request, "encodings done!")
        return HttpResponseRedirect("../")

    @method_decorator(login_required(login_url='/admin/login'))
    def load_files(self, request):
        x.load_files()
        self.message_user(request, "files loaded!")
        return HttpResponseRedirect("../")

    def image_tag(self, obj):
        return mark_safe('<img src="{url}" height={height} />'.format(
            url = obj.file.url,
            height=150,
        )
    )



    image_tag.short_description = 'Image'
admin.site.register(Log, LogAdmin)
admin.site.register(Person, PersonAdmin)
admin.site.site_header = "Smart Gate Administration"

