# -*- coding: utf-8 -*-
import gzip
import io
import json
import time
from urllib.parse import urlencode
from urllib.request import urlopen, Request

from django.contrib import auth, messages
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm
from django.core import paginator
from django.core.paginator import PageNotAnInteger, EmptyPage, Paginator
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib.auth import login as auth_login
from selenium import webdriver
from selenium.webdriver.common.by import By

from checkpapers.settings import CHROMEDRIVER_PATH
from main.forms import PaperForm
from misc.checkPapers import checkPaper, createPaper, getShilds, SHILD_LENGTH
from .models import Greeting, Paper
from json import dumps, loads, JSONEncoder, JSONDecoder
import pickle
from lxml import etree


class PythonObjectEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (list, dict, str, int, float, bool, type(None))):
            return JSONEncoder.default(self, obj)
        return {'_python_object': pickle.dumps(obj)}


def as_python_object(dct):
    if '_python_object' in dct:
        return pickle.loads(str(dct['_python_object']))
    return dct


# Create your views here.
def index(request):
    # return HttpResponse('Hello from Python!')
    return render(request, "index.html")


# Create your views here.
def test(request):
    # return HttpResponse('Hello from Python!')
    return render(request, "testPage.html")


def encodeData(data):
    buffer = io.BytesIO(data)  # Use StringIO.StringIO(response.read()) in Python 2
    gzipped_file = gzip.GzipFile(fileobj=buffer)
    decoded = gzipped_file.read()
    return decoded.decode("utf-8")  # Replace utf-8 with the source encoding of your requested resource


def loadUrls(request):
    # если post запрос
    if request.method == 'POST':
        user_agent = "'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5)\
                AppleWebKit/537.36 (KHTML, like Gecko) Cafari/537.36'"
        # for shild in request.session["shilds"]:
        options = webdriver.ChromeOptions()
        # options.add_argument('headless')
        # options.add_argument('window-size=1920x1080')
        # options.add_argument("disable-gpu")
        urls = []
        driver = webdriver.Chrome(CHROMEDRIVER_PATH, options=options)

        url = "http://yandex.ru/search"
        headers = {'User-Agent': user_agent, }

        if request.POST["state"] == "captcha":
            # print(request.POST)
            url = "http://yandex.ru/checkcaptcha"
            data = {}
            data["rep"] = str(request.POST["code"])
            data["key"] = str(request.POST["key"])
            data["retpath"] = str(request.POST["retpath"])
            url_values = urlencode(data)
            # print(url + '?' + url_values)
            request = Request(url + '?' + url_values, None, headers)
            response = urlopen(request)
            data = response.read()
            # print(str(data, 'utf-8'))
        else:
            urls = set()
            for shild in request.session["shilds"]:
                print(shild)
                query = urlencode({'text': '"' + shild + '"'})
                # print(url + query)
                # request = Request(url + '?' + query, None, headers)
                driver.get(url + '?' + query)
                captchaImgs = driver.find_elements_by_xpath("//div[@class='captcha__image']/img")
                # print(captchaImgs)
                if len(captchaImgs) > 0:
                    key = driver.find_element_by_xpath("//*[@class='form__key']/@value")
                    # print(key)
                    retpath = driver.find_element_by_xpath("//*[@class='form__retpath']/@value")
                    # print(retpath)
                    return JsonResponse({
                        "state": "needCaptcha",
                        "captcha": captchaImgs[0].attrib["src"],
                        "key": key,
                        "retpath": retpath
                    })
                for link in driver.find_elements_by_xpath('//a'):
                    strLink = str(link.get_attribute("href"))
                    if (not "yandex" in strLink) and (not "bing" in strLink) and (not "google" in strLink) and (
                            not "mail" in strLink) and (strLink is not None):
                        urls.add(strLink)
                        #print(strLink)
            # if link.startswith('/url?q=') and not link.contains("google.com"):
            # print(link)
            print("ready")
        return JsonResponse({"state": "ready"})
    else:
        messages.error(request, "этот метод можно вызывать только через POST запрос")
        return HttpResponseRedirect("personal")


def loadUrlsGoogle(request):
    # если post запрос
    if request.method == 'POST':
        user_agent = "'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5)\
                AppleWebKit/537.36 (KHTML, like Gecko) Cafari/537.36'"
        # for shild in request.session["shilds"]:
        url = "https://www.google.com/search"
        headers = {'User-Agent': user_agent, }
        options = webdriver.ChromeOptions()
        # options.add_argument('headless')
        # options.add_argument('window-size=1920x1080')
        # options.add_argument("disable-gpu")
        urls = []
        driver = webdriver.Chrome(CHROMEDRIVER_PATH, options=options)
        for shild in request.session["shilds"]:
            print(shild)
            query = urlencode({'q': '"' + shild + '"'})
            driver.get('http://www.google.com/search?' + query)
            if len(driver.find_elements_by_xpath("//a[@href]")) == 0:
                print("+++++++++++++++++++++ERROR+++++++++++++++++++++++++")
                print(driver.page_source)
                return JsonResponse({"state": "needCaptcha"})

            for link in driver.find_elements_by_xpath("//a[@href]"):
                strLink = str(link.get_attribute("href"))
                if strLink == "http://www.google.ru/policies/terms/":
                    return JsonResponse({"state": "needCaptcha"})
                if (not "www.google.com" in strLink) and (not "www.google.ru" in strLink) and (
                        not "maps.google.com" in strLink) and (
                        not "support.google.com" in strLink) and (not "policies.google.com" in strLink):
                    urls.append(link.get_attribute('href'))

        print("ready")
        print(urls)
        checkPaper(request.session["shilds"], urls)
        return JsonResponse({"state": "ready"})
    else:
        messages.error(request, "этот метод можно вызывать только через POST запрос")
        return HttpResponseRedirect("personal")


# Create your views here.
def check(request):
    # return HttpResponse('Hello from Python!')
    if not request.user.is_authenticated:
        return HttpResponseRedirect("/needlogin")

    # если post запрос
    if request.method == 'POST':
        # строим форму на основе запроса
        form = PaperForm(request.POST)
        # если форма заполнена корректно
        if form.is_valid():
            data = {
                'text': form.cleaned_data["text"],
                'name': form.cleaned_data["name"],
            }
            # проверяем, что пароли совпадают
            if form.cleaned_data["text"] == "":
                # выводим сообщение и перезаполняем форму
                messages.error(request, "Вы послали на проверку статью без текста")
                # проверяем, что пароли совпадают
            elif form.cleaned_data["name"] == "":
                # выводим сообщение и перезаполняем форму
                messages.error(request, "Вы послали на проверку статью без текста")
            else:
                request.session["urls"] = []
                request.session["shilds"] = getShilds(form.cleaned_data["text"], SHILD_LENGTH)
                request.session["currentShild"] = ""
                request.session["text"] = form.cleaned_data["text"]
                request.session["name"] = form.cleaned_data["name"]
                return JsonResponse({"state": "readyToLoad"})
            # перерисовываем окно
            return render(request, "check.html", {
                'form': PaperForm(initial=data),
            })
        else:
            # перезагружаем страницу
            messages.error(request, "Неправильно заполнена форма")

            return HttpResponseRedirect("check")
    else:
        # возвращаем простое окно регистрации
        return render(request, "check.html", {
            'form': PaperForm()
        })


# Create your views here.
def checkWithYandex(request):
    # return HttpResponse('Hello from Python!')
    if not request.user.is_authenticated:
        return HttpResponseRedirect("/needlogin")

    # если post запрос
    if request.method == 'POST':
        # строим форму на основе запроса
        form = PaperForm(request.POST)
        # если форма заполнена корректно
        if form.is_valid():
            data = {
                'text': form.cleaned_data["text"],
                'name': form.cleaned_data["name"],
            }
            # проверяем, что пароли совпадают
            if form.cleaned_data["text"] == "":
                # выводим сообщение и перезаполняем форму
                messages.error(request, "Вы послали на проверку статью без текста")
                # проверяем, что пароли совпадают
            elif form.cleaned_data["name"] == "":
                # выводим сообщение и перезаполняем форму
                messages.error(request, "Вы послали на проверку статью без текста")
            else:
                [u, t] = createPaper(form.cleaned_data["text"], form.cleaned_data["name"], request.user)
                if u < 0:
                    messages.error(request, "Ошибка API поиска")
                    return HttpResponseRedirect("/check")
                else:
                    messages.info(request, "Уникальность текста: " + f"{u:.{1}f}%".format(
                        u) + ", правдивость: " + f"{t:.{1}f}%".format(t))
                return HttpResponseRedirect("/personal")
            # перерисовываем окно
            return render(request, "check.html", {
                'form': PaperForm(initial=data),
            })
        else:
            # перезагружаем страницу
            messages.error(request, "Неправильно заполнена форма")

            return HttpResponseRedirect("check")
    else:
        # возвращаем простое окно регистрации
        return render(request, "check.html", {
            'form': PaperForm()
        })


# Create your views here.
def about(request):
    # return HttpResponse('Hello from Python!')
    return render(request, "about.html")


def personalFirsPage(request):
    return personal(request, 1)


# Create your views here.
def personal(request, page):
    # return HttpResponse('Hello from Python!')
    if request.user.is_authenticated:
        paginator = Paginator(Paper.objects.all().filter(author=request.user), 12)
        try:
            papers = paginator.page(page)
        except PageNotAnInteger:
            papers = paginator.page(1)
        except EmptyPage:
            papers = paginator.page(paginator.num_pages)

        return render(request, "papers.html", {
            "papers": papers,
            "paperCount": len(papers),
            "flgAllPapers": False,
            "page": page
        })
    else:
        return HttpResponseRedirect("/needlogin")


def papersFirsPage(request):
    return papers(request, 1)


# Create your views here.
def papers(request, page):
    # return HttpResponse('Hello from Python!')
    if request.user.is_authenticated:
        paginator = Paginator(Paper.objects.all(), 12)
        try:
            papers = paginator.page(page)
        except PageNotAnInteger:
            papers = paginator.page(1)
        except EmptyPage:
            papers = paginator.page(paginator.num_pages)

        return render(request, "papers.html", {
            "papers": papers,
            "paperCount": len(papers),
            "flgAllPapers": True,
            "page": page
        })
    else:
        return HttpResponseRedirect("/needlogin")


def deletePaper(request, paper_id):
    # return HttpResponse('Hello from Python!')
    if not request.user.is_authenticated:
        return HttpResponseRedirect("/needlogin")

    try:
        paper = Paper.objects.get(pk=paper_id)
        if not request.user == paper.author:
            messages.error(request, "Вы не можете удалять чужые статьи")
        else:
            paper.delete()
            messages.info(request, "Статья удалена")
    except:
        messages.error(request, "статья с id " + str(paper_id) + " не найдена")

    return HttpResponseRedirect("/personal")


def needLogin(request):
    # return HttpResponse('Hello from Python!')
    return render(request, "needlogin.html")


def readPaper(request, paper_id):
    try:
        paper = Paper.objects.get(pk=paper_id)
        return render(request, "readPaper.html", {
            "paper": paper
        })
    except:
        messages.error(request, "статья с id " + str(paper_id) + " не найдена")
        return HttpResponseRedirect("/personal")
