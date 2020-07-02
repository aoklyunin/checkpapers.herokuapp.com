# coding=utf-8
# программа для загрузки оценок
import datetime

from django.contrib.auth.models import User
from django.core.management import BaseCommand
import wikipedia as wikipedia
from django.contrib.auth.models import User
from requests import get

from main.models import Paper
## importing socket module
import socket

# описание класса програмы
class Command(BaseCommand):
    # описание программы
    helf = 'remove loaded textes from wiki'

    def handle(self, *args, **options):
        ip = get('https://api.ipify.org').text
        print('My public IP address is:', ip)

