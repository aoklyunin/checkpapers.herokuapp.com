from django.contrib import admin

# Register your models here.
from main.models import Paper

class PaperAdmin(admin.ModelAdmin):
    list_display = ('text', 'author', 'uniquenessPercent')

admin.site.register(Paper,PaperAdmin)
