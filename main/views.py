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
from misc.check_papers import check_paper, get_shilds
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
        # эта опция используется только для деплоя на heroku
        #options.binary_location = os.environ.get('GOOGLE_CHROME_BIN')
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
            for cookie in request.session["cookies"]:
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
            # загуржаем страницу поиска по шилду
            shild = request.session["shilds"][i]
            query = urlencode({'text': '"' + shild + '"'})
            url = "http://yandex.ru/search"
            driver.get(url + '?' + query)
            # ищем картинку с капчей
            captcha_imgs = driver.find_elements_by_xpath("//div[@class='captcha__image']/img")
            # если нашли картинку
            if len(captcha_imgs) > 0:
                # сохраняем уже обработанные ссылки
                request.session["urls"] = list(urls)
                # сохраняем куки
                request.session["cookies"] = driver.get_cookies()
                # получаем параметры капчи
                captcha = captcha_imgs[0].get_attribute("src")
                key = driver.find_element_by_xpath("//*[@class='form__key']").get_attribute("value")
                retpath = driver.find_element_by_xpath("//*[@class='form__retpath']").get_attribute("value")
                driver_url = driver.current_url
                return JsonResponse({
                    "state": "needCaptcha",
                    "captcha": captcha,
                    "url": driver_url,
                    "key": key,
                    "retpath": retpath,
                })
            # перебираем все ссылки на странице
            for link in driver.find_elements_by_xpath('//a'):
                # добавляем только те, которые ссылаются не на яндекс
                str_link = str(link.get_attribute("href"))
                if (not "yandex" in str_link) and (not "bing" in str_link) and (not "google" in str_link) and (
                        not "mail" in str_link) and (str_link is not None):
                    urls.add(str_link)
            # увеличиваем номер текущего шилда на 1
            request.session["currentShild"] = request.session["currentShild"] + 1
        # сохраняем уже обработанные ссылки
        request.session["urls"] = list(urls)
        return JsonResponse({"state": "ready"})
    else:
        messages.error(request, "этот метод можно вызывать только через POST запрос")
        return HttpResponseRedirect("personal")


# обработка загруженных ссылок
def process_urls(request):
    [u, t] = check_paper(request.session["shilds"], request.session["urls"])
    # на всякий случай очищаем переменные сессии
    request.session["urls"] = []
    request.session["shilds"] = []
    # из-за долгого времени ожидания соединение обрывается
    # нужно его перезапускать
    connection.connect()
    # создаём запись о статье
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


# проверка статьи
def check(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect("/need_login")

    # если post запрос
    if request.method == 'POST':
        # строим форму на основе запроса
        form = PaperForm(request.POST)
        # если форма заполнена корректно
        if form.is_valid():
            # проверяем, что у статьи есть текст
            if form.cleaned_data["text"] == "":
                # выводим сообщение и перезаполняем форму
                messages.error(request, "Вы послали на проверку статью без текста")
                return HttpResponseRedirect("check")
            # проверяем, что у статьи есть название
            elif form.cleaned_data["name"] == "":
                # выводим сообщение и перезаполняем форму
                messages.error(request, "Вы послали на проверку статью без названия")
                return HttpResponseRedirect("check")
            # проверяем, что у в статье достаточное кол-во слов
            else:
                shilds = get_shilds(form.cleaned_data["text"])
                if len(shilds) == 0:
                    messages.error(request, "Статья содержит слдишком мало слов")
                    return JsonResponse({"state": "formError"})
                request.session["urls"] = []
                request.session["shilds"] = shilds
                request.session["currentShild"] = 0
                request.session["text"] = form.cleaned_data["text"]
                request.session["name"] = form.cleaned_data["name"]
                return JsonResponse({"state": "readyToLoad"})
        else:
            # перезагружаем страницу
            messages.error(request, "Неправильно заполнена форма")
            return HttpResponseRedirect("check")
    else:
        # возвращаем простое окно регистрации
        return render(request, "check.html", {
            'form': PaperForm()
        })


# страница "О проекте"
def about(request):
    return render(request, "about.html")


# первая страница раздела "Мои статьи"
def personal_firs_page(request):
    return personal(request, 1)


# раздел "Мои статьи"
def personal(request, page):
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


# первая страница раздела "Cтатьи"
def papers_first_page(request):
    return papers(request, 1)


# раздел "Cтатьи"
def papers(request, page):
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


# удалить статью
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


# страница с предупреждением о необходимости авторизации
def need_login(request):
    # return HttpResponse('Hello from Python!')
    return render(request, "need_login.html")


# страница с отображением выбранной статьи
def read_paper(request, paper_id):
    try:
        paper = Paper.objects.get(pk=paper_id)
        return render(request, "read_paper.html", {
            "paper": paper
        })
    except:
        messages.error(request, "статья с id " + str(paper_id) + " не найдена")
        return HttpResponseRedirect("/personal")
