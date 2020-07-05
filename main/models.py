# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from django.db import models
from django_postgres_unlimited_varchar import UnlimitedCharField


# модель статьи
class Paper(models.Model):
    # название статьи
    name = UnlimitedCharField(default="")
    # текст
    text = UnlimitedCharField()
    # автор
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    # процент уникальности
    uniquenessPercent = models.FloatField(default=-1)
    # правдивость статьи
    truth = models.FloatField(default=-1)


# параметры статьи при добавлении
class AddPaperConf(models.Model):
    # текст
    text = UnlimitedCharField(default="")
    # название статьи
    name = UnlimitedCharField(default="")
    # начальное времяDate
    start_time = models.DateTimeField(auto_now=True, auto_now_add=False)
    # кол-во сайтов для проверки
    check_url_cnt = models.IntegerField(default=0)
    # пользователь, добавляющий статью
    author = models.ForeignKey(User, on_delete=models.CASCADE, default=None)


# URL для добавления
class UrlToProcess(models.Model):
    # значение
    value = UnlimitedCharField(default="")
    # пользователь, создавший шилды
    author = models.ForeignKey(User, on_delete=models.CASCADE, default=None)
    # флаг, что проверка не удалась
    flg_process_error = models.BooleanField(default=False)


# шилд для добавления
class ShildToProcess(models.Model):
    # значение
    value = UnlimitedCharField(default="")
    # флаг, нужно ли удалять во время поиска ссылок
    to_delete = models.BooleanField(default=False)
    # пользователь, создавший шилды
    author = models.ForeignKey(User, on_delete=models.CASCADE, default=None)
    # сколько раз найден данный шилд в статьях
    founded_cnt = models.IntegerField(default=0)


# ещё не использованные для обработки статьи
class NotUsedPaper(models.Model):
    # статья
    paper = models.ForeignKey(Paper, on_delete=models.CASCADE, default=None)
    # пользователь, создавший шилд
    author = models.ForeignKey(User, on_delete=models.CASCADE, default=None)


class ShildFromURLText(models.Model):
    # текст шилда
    value = UnlimitedCharField(default="")
    # пользователь, создавший шилды
    url = models.ForeignKey(UrlToProcess, on_delete=models.CASCADE, default=None)
    # пользователь, создавший шилд
    author = models.ForeignKey(User, on_delete=models.CASCADE, default=None)


class ShildFromNotUsedPaper(models.Model):
    # текст шилда
    value = UnlimitedCharField(default="")
    # пользователь, создавший шилды
    paper = models.ForeignKey(NotUsedPaper, on_delete=models.CASCADE, default=None)
    # пользователь, создавший шилды
    author = models.ForeignKey(User, on_delete=models.CASCADE, default=None)
