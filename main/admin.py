# -*- coding: utf-8 -*-
from django.contrib import admin
from main.models import Paper

class PaperAdmin(admin.ModelAdmin):
    list_display = ('text', 'author', 'uniquenessPercent')

admin.site.register(Paper,PaperAdmin)
