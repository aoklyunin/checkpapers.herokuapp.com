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
