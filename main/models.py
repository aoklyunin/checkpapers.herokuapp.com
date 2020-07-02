from django.contrib.auth.models import User
from django.db import models

# Create your models here.
from django_postgres_unlimited_varchar import UnlimitedCharField


class Greeting(models.Model):
    when = models.DateTimeField("date created", auto_now_add=True)


class Paper(models.Model):
    text = UnlimitedCharField()
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    uniquenessPercent = models.FloatField(default=-1)
    truth = models.FloatField(default=-1)
    name = UnlimitedCharField(default="")
