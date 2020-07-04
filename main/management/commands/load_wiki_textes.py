# coding=utf-8
from django.core.management import BaseCommand
import wikipedia as wikipedia
from django.contrib.auth.models import User
from main.models import Paper
from misc.check_papers import check_paper_with_yandex_api
from django.db import connection


# получить случайную статью из википедии
def get_wiki_random_article():
    random = wikipedia.random(1)
    try:
        result = wikipedia.page(random).summary
    except wikipedia.exceptions.DisambiguationError as e:
        result = get_wiki_random_article()
    return result


# загрузить заданное число статей из википедии и проверить
class Command(BaseCommand):
    # описание программы
    helf = 'load textes from wiki'

    def add_arguments(self, parser):
        parser.add_argument('paper_cnt', nargs='+', type=int)

    def handle(self, *args, **options):
        user = User.objects.get(username="test")
        for i in range(options['paper_cnt'][0]):
            text = get_wiki_random_article()
            name = text[:100] if len(text) > 100 else text
            print(str(i) + ": " + name)
            print(self.create_paper(
                author=user,
                name=name,
                text=text,
            ))

    # создать стаью
    @staticmethod
    def create_paper(text, name, author):
        [u, t] = check_paper_with_yandex_api(text)
        if u == -1:
            return [u, t]
        # из-за долгого времени ожидания соединение обрывается
        # нужно его перезапускать
        connection.connect()
        Paper.objects.create(
            name=name,
            author=author,
            text=text,
            uniquenessPercent=u,
            truth=t
        )
        return [u, t]
