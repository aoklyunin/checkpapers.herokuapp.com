# -*- coding: utf-8 -*-
import os
import time

from django.db import connection
from urllib.parse import urlencode
from django.contrib import messages
from django.core.paginator import PageNotAnInteger, EmptyPage, Paginator
from django.shortcuts import render
from django.http import HttpResponseRedirect, JsonResponse
from selenium import webdriver
from main.forms import PaperForm
from misc.checkPapers import checkPaper, getShilds, SHILD_LENGTH
from .models import Paper


# главная страница
def index(request):
    return render(request, "index.html")


# загрузить ссылки на статьи
def load_urls(request):
    # если post запрос
    if request.method == 'POST':
        # опции веб-драйвера
        options = webdriver.ChromeOptions()
        options.binary_location = os.environ.get('GOOGLE_CHROME_BIN')
        options.add_argument('headless')
        options.add_argument("disable-gpu")
        options.add_argument('no-sandbox')
        options.add_argument('disable-dev-shm-usage')
        # создаём драйвер
        driver = webdriver.Chrome(str(os.environ.get('CHROMEDRIVER_PATH')), options=options)
        # если нужно ввести капчу
        if request.POST["state"] == "captcha":
            # переходим на по сохранённому адресу страницы с капчей
            driver.get(request.POST["url"])
            time.sleep(0.5)
            # восстанавливаем куки
            print("cookies:")
            for cookie in request.session["cookies"]:
                print(" " + str(cookie))
                driver.add_cookie(cookie)
            # подменяем значения скрытых полей(яндекс при каждой загрузке даёт новую капчу)
            key_elem = driver.find_element_by_xpath("//*[@class='form__key']")
            driver.execute_script("arguments[0].value = '" + request.POST["key"] + "';", key_elem)
            key_ret_path = driver.find_element_by_xpath("//*[@class='form__retpath']")
            driver.execute_script("arguments[0].value = '" + request.POST["retpath"] + "';", key_ret_path)
            # отправляем код капчи
            input_elem = driver.find_element_by_xpath("/html/body/div/form/div[3]/div[1]/input")
            input_elem.send_keys(request.POST["code"])
            submit = driver.find_element_by_xpath("/html/body/div/form/button")
            submit.click()

        # множество ссылок
        urls = set()
        # добавляем в него список всех уже сохранённых ссылок
        urls.update(request.session["urls"])
        # перебираем необработанные шилды(начинаются с номера currentShild)
        for i in range(request.session["currentShild"], len(request.session["shilds"])):
            shild = request.session["shilds"][i]
            query = urlencode({'text': '"' + shild + '"'})
            url = "http://yandex.ru/search"
            driver.get(url + '?' + query)
            captcha_imgs = driver.find_elements_by_xpath("//div[@class='captcha__image']/img")
            # print(captchaImgs)
            if len(captcha_imgs) > 0:
                print("get captcha")
                request.session["urls"] = list(urls)
                # request.session["session_id"] = driver.session_id
                request.session["cookies"] = driver.get_cookies()
                captcha = captcha_imgs[0].get_attribute("src")
                key = driver.find_element_by_xpath("//*[@class='form__key']").get_attribute("value")
                # print(key)
                retpath = driver.find_element_by_xpath("//*[@class='form__retpath']").get_attribute("value")
                driver_url = driver.current_url
                return JsonResponse({
                    "state": "needCaptcha",
                    "captcha": captcha,
                    "url": driver_url,
                    "key": key,
                    "retpath": retpath,
                })
            print("load links")
            for link in driver.find_elements_by_xpath('//a'):
                str_link = str(link.get_attribute("href"))
                if (not "yandex" in str_link) and (not "bing" in str_link) and (not "google" in str_link) and (
                        not "mail" in str_link) and (str_link is not None):
                    urls.add(str_link)
            request.session["currentShild"] = request.session["currentShild"] + 1
            # print(strLink)
        # if link.startswith('/url?q=') and not link.contains("google.com"):
        # print(link)
        print("ready")
        request.session["urls"] = list(urls)
        return JsonResponse({"state": "ready"})
    else:
        messages.error(request, "этот метод можно вызывать только через POST запрос")
        return HttpResponseRedirect("personal")


def process_urls(request):
    print("process_urls")
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
        return HttpResponseRedirect("/need_login")

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
def about(request):
    # return HttpResponse('Hello from Python!')
    return render(request, "about.html")


def personal_firs_page(request):
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
        return HttpResponseRedirect("/need_login")


def papers_first_page(request):
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
        return HttpResponseRedirect("/need_login")


def delete_paper(request, paper_id):
    # return HttpResponse('Hello from Python!')
    if not request.user.is_authenticated:
        return HttpResponseRedirect("/need_login")

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


def need_login(request):
    # return HttpResponse('Hello from Python!')
    return render(request, "need_login.html")


def readPaper(request, paper_id):
    try:
        paper = Paper.objects.get(pk=paper_id)
        return render(request, "read_paper.html", {
            "paper": paper
        })
    except:
        messages.error(request, "статья с id " + str(paper_id) + " не найдена")
        return HttpResponseRedirect("/personal")
