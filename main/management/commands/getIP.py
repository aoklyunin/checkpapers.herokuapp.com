# coding=utf-8
from django.core.management import BaseCommand
from requests import get

# описание класса програмы
class Command(BaseCommand):
    # описание программы
    helf = 'remove loaded textes from wiki'

    def handle(self, *args, **options):
        ip = get('https://api.ipify.org').text
        print('My public IP address is:', ip)
