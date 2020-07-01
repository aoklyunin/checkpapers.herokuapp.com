# coding=utf-8
# программа для загрузки оценок
import datetime

from django.contrib.auth.models import User
from django.core.management import BaseCommand
import wikipedia as wikipedia
from django.contrib.auth.models import User

from main.models import Paper
from misc.checkPapers import createPaper


def random_page():
    random = wikipedia.random(1)
    try:
        result = wikipedia.page(random).summary
    except wikipedia.exceptions.DisambiguationError as e:
        result = random_page()
    return result


# описание класса програмы
class Command(BaseCommand):
    # описание программы
    helf = 'load textes from wiki'

    def add_arguments(self, parser):
        parser.add_argument('paper_cnt', nargs='+', type=int)

    def handle(self, *args, **options):
        user = User.objects.get(username="test")
        for i in range(options['paper_cnt'][0]):
            print(i)
            text = random_page()
            print(createPaper(
                author=user,
                text=text
            ))
            print(text)
