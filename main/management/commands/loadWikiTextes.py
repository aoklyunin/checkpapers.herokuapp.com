# coding=utf-8
from django.core.management import BaseCommand
import wikipedia as wikipedia
from django.contrib.auth.models import User

from misc.checkPapers import createPaper, createPaperYandex


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
            text = random_page()
            name = text[:100] if len(text) > 100 else text
            print(str(i) + ": " + name)
            print(createPaperYandex(
                author=user,
                name=name,
                text=text,
            ))
