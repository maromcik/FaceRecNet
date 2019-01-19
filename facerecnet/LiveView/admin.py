from django.contrib import admin
from LiveView.models import Person, Log, Setting
from django.utils.safestring import mark_safe
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.urls import path
from LiveView import views
from django.http import HttpResponseRedirect
import socket


class LogAdmin(admin.ModelAdmin):
    list_display = ['person', 'time', 'granted', 'image_tag']
    list_filter = ['time', 'granted']
    search_fields = ['person__name']
    readonly_fields = ['person', 'time', 'granted', 'snapshot']

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


    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('encoding/', self.run_encodings),
            path('load/', self.load_files),
        ]
        return my_urls + urls

    @method_decorator(login_required(login_url='/admin/login'))
    def run_encodings(self, request):
        views.rec_threads.rec.load_files()
        views.rec_threads.rec.known_subjects_descriptors()
        views.rec_threads.rec.load_files()
        self.message_user(request, "Encodings done!")
        return HttpResponseRedirect("../")

    @method_decorator(login_required(login_url='/admin/login'))
    def load_files(self, request):
        views.rec_threads.rec.load_files()
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
    fields = ['device', 'crop', 'subscription']
    list_display = ['device', 'crop', 'subscription']
    change_list_template = "LiveView/change_list2.html"

    def has_add_permission(self, request, obj=None):
        return False

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('grab/', self.grab_cap),
            path('load/', self.load_files),
            path('reconnect/', self.reconnect),
        ]
        return my_urls + urls

    @method_decorator(login_required(login_url='/admin/login'))
    def load_files(self, request):
        views.rec_threads.rec.load_files()
        self.message_user(request, "Files loaded!")
        return HttpResponseRedirect("../")


    @method_decorator(login_required(login_url='/admin/login'))
    def grab_cap(self, request):
        try:
            if views.rec_threads.facerecognition_thread.isAlive():
                views.rec_threads.rec.load_files()
                views.rec_threads.rec.grab_cap()
                views.rec_threads.startrecognition()
                self.message_user(request, "Capture grabbed!")
                return HttpResponseRedirect("../")
            else:
                self.message_user(request, "Face recognition is not running!")
                return HttpResponseRedirect("../")
        except AttributeError:
            self.message_user(request, "Face recognition is not running!")
            return HttpResponseRedirect("../")


    @method_decorator(login_required(login_url='/admin/login'))
    def reconnect(self, request):
        try:
            if views.rec_threads.facerecognition_thread.isAlive():
                views.rec_threads.rec.c.shutdown(2)
                views.rec_threads.rec.c.close()
                views.rec_threads.rec.s.shutdown(2)
                views.rec_threads.rec.s.close()
                print("connection closed")
                views.rec_threads.rec.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                views.rec_threads.rec.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                views.rec_threads.rec.s.bind((views.rec_threads.rec.host, views.rec_threads.rec.port1))
                views.rec_threads.rec.s.listen(1)
                views.rec_threads.rec.c, addr = views.rec_threads.rec.s.accept()
                print(addr, " connected")
                views.rec_threads.startrecognition()
                self.message_user(request, "Arduino reconnected!")
                return HttpResponseRedirect("../")
            else:
                self.message_user(request, "Face recognition is not running!")
                return HttpResponseRedirect("../")
        except AttributeError:
            self.message_user(request, "There's a problem with the Arduino, try to restart it!")
            return HttpResponseRedirect("../")


admin.site.register(Person, PersonAdmin)
admin.site.register(Log, LogAdmin)
admin.site.register(Setting, SettingAdmin)
admin.site.site_header = "Smart Gate Administration"


