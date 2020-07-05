# -*- coding: utf-8 -*-
from django.contrib import admin
from main.models import Paper, AddPaperConf, UrlToProcess, ShildToProcess, NotUsedPaper, ShildFromURLText, \
    ShildFromNotUsedPaper


class PaperAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'uniquenessPercent', 'truth')


class AddPaperConfAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_time', 'author', 'check_url_cnt')


class UrlToProcessAdmin(admin.ModelAdmin):
    list_display = ('value', 'author')


class ShildToProcessAdmin(admin.ModelAdmin):
    list_display = ('value', 'to_delete', 'author', 'founded_cnt')


class NotUsedPaperAdmin(admin.ModelAdmin):
    list_display = ('paper', 'author')


class ShildFromURLTextAdmin(admin.ModelAdmin):
    list_display = ('url', 'value', 'author')


class ShildFromNotUsedPaperAdmin(admin.ModelAdmin):
    list_display = ('paper', 'paper', 'author')



admin.site.register(Paper, PaperAdmin)

admin.site.register(AddPaperConf, AddPaperConfAdmin)
admin.site.register(UrlToProcess, UrlToProcessAdmin)
admin.site.register(ShildToProcess, ShildToProcessAdmin)
admin.site.register(NotUsedPaper, NotUsedPaperAdmin)
admin.site.register(ShildFromURLText, ShildFromURLTextAdmin)
admin.site.register(ShildFromNotUsedPaper, ShildFromNotUsedPaperAdmin)
