# -*- coding: utf-8 -*-
import os
import time
from django.db import connection
from urllib.parse import urlencode
from django.contrib import messages
from django.core.paginator import PageNotAnInteger, EmptyPage, Paginator
from django.shortcuts import render
from django.http import HttpResponseRedirect, JsonResponse
from django.utils.timezone import now
from selenium import webdriver
from main.forms import PaperForm
from main.process import process_urls_start, process_papers, process_urls_body, save_paper
from misc.check_papers import get_shilds
from .models import Paper, AddPaperConf, ShildToProcess, UrlToProcess


# главная страница
def index(request):
    return render(request, "index.html")


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
                # на всякий случай удаляем все параметры
                AddPaperConf.objects.all().filter(author=request.user).delete()

                # создаём параметры добавления статьи
                AddPaperConf.objects.create(
                    text=form.cleaned_data["text"],
                    name=form.cleaned_data["name"],
                    author=request.user,
                    start_time=now()
                )
                # очищаем шилды
                ShildToProcess.objects.all().filter(author=request.user).delete()
                # очищаем ссылки
                UrlToProcess.objects.all().filter(author=request.user).delete()
                # сохраняем шилды для поиска и последующего удаления
                ShildToProcess.objects.bulk_create([ShildToProcess(**{
                    'value': m,
                    'to_delete': False,
                    'author': request.user,
                    'founded_cnt': 0
                }) for m in shilds])
                # сохраняем шилды для обработки
                ShildToProcess.objects.bulk_create([ShildToProcess(**{
                    'value': m,
                    'to_delete': True,
                    'author': request.user,
                    'founded_cnt': 0
                }) for m in shilds])
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


# загрузить ссылки на статьи
def load_urls(request):
    # если post запрос
    if request.method == 'POST':
        # время начала загрузки
        start_time = time.time()
        # опции веб-драйвера
        options = webdriver.ChromeOptions()
        # эта опция используется только для деплоя на heroku
        options.binary_location = os.environ.get('GOOGLE_CHROME_BIN')
        options.add_argument('--headless')
        options.add_argument("--disable-gpu")
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--ignore-certificate-errors')
        # создаём драйвер
        driver = webdriver.Chrome(str(os.environ.get('CHROMEDRIVER_PATH')), options=options)
        # флаг, что найдена капча
        flg_get_captcha = False

        # если нужно ввести капчу
        if request.POST["state"] == "captcha":
            flg_get_captcha = True
            # переходим на по сохранённому адресу страницы с капчей
            driver.get(request.POST["url"])
            time.sleep(0.5)
            # восстанавливаем куки
            for cookie in request.session["driver-cookies"]:
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
        # если мы продолжаем загрузку
        elif request.POST["state"] == "continue":
            # восстанавливаем куки
            driver.get('http://yandex.ru/')
            for cookie in request.session["driver-cookies"]:
                driver.add_cookie(cookie)

        # множество ссылок
        urls = set()
        # добавляем в него список всех уже сохранённых ссылок
        urls.update([url_to_process.value for url_to_process in UrlToProcess.objects.all().filter(author=request.user)])

        # получаем общее кол-во шилдов статьи
        shild_cnt = len(ShildToProcess.objects.all().filter(to_delete=False))
        # перебираем необработанные шилды
        for shild in ShildToProcess.objects.all().filter(to_delete=True):
            # если превышено максимальное время выполнения скрипта
            if time.time() - start_time > MAX_SCRIPT_PROCESS_TIME:
                # сохраняем уже обработанные ссылки
                UrlToProcess.objects.all().filter(author=request.user).delete()
                UrlToProcess.objects.bulk_create([UrlToProcess(**{'value': m, 'author': request.user}) for m in urls])
                # сохраняем куки
                request.session["driver-cookies"] = driver.get_cookies()
                driver.quit()
                shilds_to_load_cnt = len(ShildToProcess.objects.all().filter(to_delete=True))
                load_percent = float(shild_cnt - shilds_to_load_cnt) / shild_cnt * 100
                return JsonResponse({
                    "state": "loadNext",
                    "process-text": "Поиск текстов: " + f"{load_percent:.{1}f}%".format(load_percent)
                })
            # если не найдена капча, выполняем новый запрос
            # (после вводы капчи, яндекс перенаправляет на последний сделанный запрос)
            if not flg_get_captcha:
                query = urlencode({'text': '"' + shild.value + '"'})
                url = "http://yandex.ru/search"
                driver.get(url + '?' + query)

            # ищем картинку с капчей
            captcha_imgs = driver.find_elements_by_xpath("//div[@class='captcha__image']/img")
            # если нашли картинку
            if len(captcha_imgs) > 0:
                # сохраняем уже обработанные ссылки
                UrlToProcess.objects.all().filter(author=request.user).delete()
                UrlToProcess.objects.bulk_create([UrlToProcess(**{'value': m, 'author': request.user}) for m in urls])
                # сохраняем куки
                request.session["driver-cookies"] = driver.get_cookies()
                # получаем параметры капчи
                captcha = captcha_imgs[0].get_attribute("src")
                key = driver.find_element_by_xpath("//*[@class='form__key']").get_attribute("value")
                retpath = driver.find_element_by_xpath("//*[@class='form__retpath']").get_attribute("value")
                driver_url = driver.current_url
                driver.quit()
                shilds_to_load_cnt = len(ShildToProcess.objects.all().filter(to_delete=True))
                load_percent = float(shild_cnt - shilds_to_load_cnt) / shild_cnt * 100
                return JsonResponse({
                    "state": "needCaptcha",
                    "process-text": "Поиск текстов: " + f"{load_percent:.{1}f}%".format(load_percent),
                    "captcha": captcha,
                    "url": driver_url,
                    "key": key,
                    "retpath": retpath,
                })
            # перебираем все ссылки на странице
            for link in driver.find_elements_by_xpath('//a'):
                # добавляем только те, которые ссылаются не на яндекс
                str_link = str(link.get_attribute("href"))
                if ("yandex" not in str_link) and ("bing" not in str_link) and ("google" not in str_link) and (
                        "mail" not in str_link) and (str_link is not None):
                    urls.add(str_link)
            # удаляем обработанный шилд
            shild.delete()
        # сохраняем уже обработанные ссылки
        UrlToProcess.objects.all().filter(author=request.user).delete()
        UrlToProcess.objects.bulk_create([UrlToProcess(**{'value': m, 'author': request.user}) for m in urls])
        return JsonResponse({"state": "ready"})
    else:
        messages.error(request, "этот метод можно вызывать только через POST запрос")
        return HttpResponseRedirect("personal")


# обработка загруженных ссылок
def process_urls(request):
    # если post запрос
    if request.method == 'POST':
        # из-за долгого времени ожидания соединение обрывается
        # нужно его перезапускать
        connection.connect()
        # получаем параметры статьи
        add_paper_conf = AddPaperConf.objects.get(author=request.user)
        # если это только начало обработки
        if request.POST["state"] == "start":
            return process_urls_start(request, add_paper_conf)

        # время начала загрузки
        start_time = time.time()

        # получаем время работы скрипта
        time_delta = (now() - add_paper_conf.start_time)
        total_seconds = time_delta.total_seconds()
        # если оно не превышает час
        if total_seconds < 60 * 60:
            # если нужно обрабатывать статьи
            if request.POST["state"] == "processPapers":
                return process_papers(request, start_time)
            if request.POST["state"] == "processUrls":
                return process_urls_body(request, add_paper_conf, start_time)

        return save_paper(request, add_paper_conf)

    else:
        messages.error(request, "этот метод можно вызывать только через POST запрос")
        return HttpResponseRedirect("personal")


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
