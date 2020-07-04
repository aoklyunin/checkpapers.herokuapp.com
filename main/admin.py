# -*- coding: utf-8 -*-
from django.contrib import admin
from main.models import Paper, AddPaperConf, UrlToProcess, ShildToProcess


class PaperAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'uniquenessPercent', 'truth')


class AddPaperConfAdmin(admin.ModelAdmin):
    list_display = ('name',)


class UrlToProcessAdmin(admin.ModelAdmin):
    list_display = ('value',)


class ShildToProcessAdmin(admin.ModelAdmin):
    list_display = ('value', 'to_delete')


admin.site.register(Paper, PaperAdmin)

admin.site.register(AddPaperConf, AddPaperConfAdmin)
admin.site.register(UrlToProcess, UrlToProcessAdmin)
admin.site.register(ShildToProcess, ShildToProcessAdmin)
