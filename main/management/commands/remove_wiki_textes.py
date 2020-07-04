# coding=utf-8
from django.core.management import BaseCommand
from django.contrib.auth.models import User
from main.models import Paper


# удалить все статьи, загруженные из википедии
class Command(BaseCommand):
    # описание программы
    helf = 'remove loaded textes from wiki'

    def handle(self, *args, **options):
        user = User.objects.get(username="test")
        Paper.objects.all().filter(author=user).delete()

