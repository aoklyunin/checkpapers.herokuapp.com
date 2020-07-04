# -*- coding: utf-8 -*-
import gzip
import io
import os

from django.db import connection

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
        # return JsonResponse({
        #     "state": "needCaptcha",
        #     "captcha": "",
        #     "url":  "",
        #     "key":  "",
        #     "retpath":  "",
        # })

        #return JsonResponse({"state": "ready"})
        options = webdriver.ChromeOptions()
        # options.binary_location = os.environ.get('GOOGLE_CHROME_BIN')
        # options.add_argument('headless')
        # options.add_argument("disable-gpu")
        # options.add_argument('no-sandbox')
        # options.add_argument('disable-dev-shm-usage')
        # options.add_experimental_option("detach", True)
        driver = webdriver.Chrome(str(os.environ.get('CHROMEDRIVER_PATH')), options=options)

        if request.POST["state"] == "captcha":
            driver.get(request.POST["url"])
            for cookie in request.session["cookies"]:
                print(cookie)
                driver.add_cookie(cookie)

            keyElem = driver.find_element_by_xpath("//*[@class='form__key']")
            driver.execute_script("arguments[0].value = '" + request.POST["key"] + "';", keyElem)
            keyRetPath = driver.find_element_by_xpath("//*[@class='form__retpath']")
            driver.execute_script("arguments[0].value = '" + request.POST["retpath"] + "';", keyRetPath)

            input = driver.find_element_by_xpath("/html/body/div/form/div[3]/div[1]/input")
            input.send_keys(request.POST["code"])
            submit = driver.find_element_by_xpath("/html/body/div/form/button")
            submit.click()

        urls = set()
        urls.update(request.session["urls"])
        for i in range(request.session["currentShild"], len(request.session["shilds"])):
            shild = request.session["shilds"][i]
            print(shild)
            query = urlencode({'text': '"' + shild + '"'})
            # print(url + query)
            # request = Request(url + '?' + query, None, headers)
            url = "http://yandex.ru/search"
            driver.get(url + '?' + query)
            captchaImgs = driver.find_elements_by_xpath("//div[@class='captcha__image']/img")
            # print(captchaImgs)
            if len(captchaImgs) > 0:
                request.session["urls"] = list(urls)
                # request.session["session_id"] = driver.session_id
                request.session["cookies"] = driver.get_cookies()
                captcha = captchaImgs[0].get_attribute("src")
                key = driver.find_element_by_xpath("//*[@class='form__key']").get_attribute("value")
                # print(key)
                retpath = driver.find_element_by_xpath("//*[@class='form__retpath']").get_attribute("value")
                driverUrl = driver.current_url
                driver.close()
                return JsonResponse({
                    "state": "needCaptcha",
                    "captcha": captcha,
                    "url": driverUrl,
                    "key": key,
                    "retpath": retpath,
                })
            for link in driver.find_elements_by_xpath('//a'):
                strLink = str(link.get_attribute("href"))
                if (not "yandex" in strLink) and (not "bing" in strLink) and (not "google" in strLink) and (
                        not "mail" in strLink) and (strLink is not None):
                    urls.add(strLink)
            request.session["currentShild"] = request.session["currentShild"] + 1
            # print(strLink)
        # if link.startswith('/url?q=') and not link.contains("google.com"):
        # print(link)
        print("ready")
        driver.close()
        request.session["urls"] = list(urls)
        return JsonResponse({"state": "ready"})
    else:
        messages.error(request, "этот метод можно вызывать только через POST запрос")
        return HttpResponseRedirect("personal")


def processUrls(request):
    print("processUrls")
    [u, t] = checkPaper(request.session["shilds"], request.session["urls"])
    request.session["urls"] = []
    request.session["shilds"] = []
    # из-за долгого времени ожидания соединение обрывается
    # нужно его перезапускать
    connection.connect()
    Paper.objects.create(
        name=request.session["name"],
        author=request.user,
        text=request.session["text"],
        uniquenessPercent=u,
        truth=t
    )
    messages.info(request, "Уникальность текста: " + f"{u:.{1}f}%".format(
        u) + ", правдивость: " + f"{t:.{1}f}%".format(t))
    return HttpResponseRedirect("/personal")


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
                request.session["currentShild"] = 0
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
        paginator = Paginator(Paper.objects.all().filter(author=request.user).order_by('pk'), 12)
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
        paginator = Paginator(Paper.objects.all().order_by('pk'), 12)
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
