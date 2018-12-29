from django.contrib import admin
from LiveView.models import Person, Log, Setting
from django.utils.safestring import mark_safe
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.urls import path
from LiveView import views
from django.http import HttpResponseRedirect


class LogAdmin(admin.ModelAdmin):
    list_display = ['person', 'time', 'granted', 'image_tag']
    list_filter = ['person', 'time', 'granted']
    search_fields = ['person__name']

    def has_add_permission(self, request, obj=None):
        return False

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
    # change_form_template = 'LiveView/change_form.html'

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('encoding/', self.run_encodings),
            path('load/', self.load_files),
        ]
        return my_urls + urls

    @method_decorator(login_required(login_url='/admin/login'))
    def run_encodings(self, request):
        views.rc.x.load_files()
        views.rc.x.known_subjects_descriptors()
        views.rc.x.load_files()
        self.message_user(request, "Encodings done!")
        return HttpResponseRedirect("../")

    @method_decorator(login_required(login_url='/admin/login'))
    def load_files(self, request):
        views.x.load_files()
        self.message_user(request, "Files loaded!")
        return HttpResponseRedirect("../")

    def image_tag(self, obj):
        return mark_safe('<img src="{url}" height={height} />'.format(
            url = obj.file.url,
            height=150,
        )
    )

    image_tag.short_description = 'Image'

class SettingAdmin(admin.ModelAdmin):
    list_display = ['device', 'crop']
    change_list_template = "LiveView/change_list2.html"

    def has_add_permission(self, request, obj=None):
        return False

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('grab/', self.grab_cap),
            path('load/', self.load_files),
        ]
        return my_urls + urls

    @method_decorator(login_required(login_url='/admin/login'))
    def load_files(self, request):
        views.x.load_files()
        self.message_user(request, "Files loaded!")
        return HttpResponseRedirect("../")


    @method_decorator(login_required(login_url='/admin/login'))
    def grab_cap(self, request):
        if views.rc.fr_thread.isAlive():
            views.rc.x.load_files()
            # views.x.release_cap()
            views.rc.x.grab_cap()
            views.rc.startrecognition()
            self.message_user(request, "Capture grabbed!")
            return HttpResponseRedirect("../")
        else:
            self.message_user(request, "Face recognition is not running!")
            return HttpResponseRedirect("../")


admin.site.register(Person, PersonAdmin)
admin.site.register(Log, LogAdmin)
admin.site.register(Setting, SettingAdmin)
admin.site.site_header = "Smart Gate Administration"


