# coding=utf-8
# программа для загрузки оценок
import datetime

from django.contrib.auth.models import User
from django.core.management import BaseCommand
import wikipedia as wikipedia
from django.contrib.auth.models import User

from main.models import Paper


# описание класса програмы
class Command(BaseCommand):
    # описание программы
    helf = 'remove loaded textes from wiki'

    def handle(self, *args, **options):
        user = User.objects.get(username="test")
        Paper.objects.all().filter(author=user).delete()

