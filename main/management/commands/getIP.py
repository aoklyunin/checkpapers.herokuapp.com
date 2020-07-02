# coding=utf-8
# программа для загрузки оценок
import datetime

from django.contrib.auth.models import User
from django.core.management import BaseCommand
import wikipedia as wikipedia
from django.contrib.auth.models import User

from main.models import Paper
## importing socket module
import socket

# описание класса програмы
class Command(BaseCommand):
    # описание программы
    helf = 'remove loaded textes from wiki'

    def handle(self, *args, **options):
        ## getting the hostname by socket.gethostname() method
        hostname = socket.gethostname()
        ## getting the IP address using socket.gethostbyname() method
        ip_address = socket.gethostbyname(hostname)
        print(ip_address)

