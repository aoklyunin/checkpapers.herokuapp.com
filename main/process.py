# -*- coding: utf-8 -*-
import time
from django.contrib import messages
from django.http import JsonResponse
from urllib.request import urlopen, Request
from wikipedia import wikipedia
from main.models import ShildFromURLText, ShildToProcess, UrlToProcess, NotUsedPaper, Paper, AddPaperConf, \
    ShildFromNotUsedPaper
from misc.check_papers import get_shilds, text_from_html, TRUTH_SHILD_CNT, MAX_SCRIPT_PROCESS_TIME


# обработка ссылок: инициализация
def process_urls_start(request, add_paper_conf):
    # создаём статьи для сверки
    NotUsedPaper.objects.bulk_create(
        [NotUsedPaper(**{'paper': paper, 'author': request.user}) for paper in Paper.objects.all()]
    )
    # сохраняем кол-во ссылок для сверки
    add_paper_conf.check_url_cnt = len(UrlToProcess.objects.all().filter(author=request.user))
    add_paper_conf.save()
    return JsonResponse({
        "state": "processPaperNext",
        "process-text": "Сверка с уже загруженными статьями..."
    })


# обработка ссылок: обработка статей
def process_papers(request, start_time):
    # получаем кол-во статей
    paper_cnt = len(Paper.objects.all())
    # если статей нет, то переходим к сверке с сайтами
    if paper_cnt == 0:
        return JsonResponse({
            "state": "completeProcessPaper",
            "process-text": "Сверка с сайтами..."
        })

    # перебираем необработанные статьи
    for non_used_paper in NotUsedPaper.objects.all().filter(author=request.user):
        # если превышено максимальное время выполнения скрипта
        if time.time() - start_time > MAX_SCRIPT_PROCESS_TIME:
            # рассчитываем процент загрузки
            non_used_paper_cnt = len(NotUsedPaper.objects.all().filter(author=request.user))
            load_percent = float(paper_cnt - non_used_paper_cnt) / paper_cnt * 100
            return JsonResponse({
                "state": "processPaperNext",
                "process-text": "Сверка с уже загруженными статьями: " + f"{load_percent:.{1}f}%".format(
                    load_percent)
            })

        # если шилды для статьи не загружены
        if len(ShildFromNotUsedPaper.objects.all().filter(paper=non_used_paper, author=request.user)) == 0:
            ShildFromNotUsedPaper.objects.bulk_create(
                [ShildFromNotUsedPaper(**{'value': m, 'paper': non_used_paper, 'author': request.user}) for m in
                 get_shilds(non_used_paper.paper.text, start_time)])

        # перебираем шилды рассматриваемой статьи
        for found_shild in ShildFromNotUsedPaper.objects.all().filter(paper=non_used_paper, author=request.user):
            # если превышено максимальное время выполнения скрипта
            if time.time() - start_time > MAX_SCRIPT_PROCESS_TIME:
                # рассчитываем процент загрузки
                non_used_paper_cnt = len(NotUsedPaper.objects.all().filter(author=request.user))
                load_percent = float(paper_cnt - non_used_paper_cnt) / paper_cnt * 100
                return JsonResponse({
                    "state": "processUrlNext",
                    "process-text": "Сверка с уже загруженными статьями: " + f"{load_percent:.{1}f}%".format(
                        load_percent)
                })
            try:
                # если шилд статьи наден в проверяемой
                current_shild_to_process = ShildToProcess.objects.get(
                    author=request.user,
                    to_delete=False,
                    value=found_shild.value
                )
                # увеличиваем его счётчик на 1
                current_shild_to_process.founded_cnt = current_shild_to_process.founded_cnt + 1
                current_shild_to_process.save()
            except:
                pass
            # удаляем обработанный шилд
            found_shild.delete()
        # удаляем обработанную статью
        non_used_paper.delete()
    return JsonResponse({
        "state": "completeProcessPaper",
        "process-text": "Сверка с сайтами..."
    })


# обработка ссылок
def process_urls_body(request, add_paper_conf, start_time):
    # перебираем необработанные ссылки
    for url_to_process in UrlToProcess.objects.all().filter(author=request.user):
        print(url_to_process.value)
        # если превышено максимальное время выполнения скрипта
        if time.time() - start_time > MAX_SCRIPT_PROCESS_TIME:
            # рассчитываем процент загрузки
            load_percent = float(add_paper_conf.check_url_cnt - len(
                UrlToProcess.objects.all().filter(
                    author=request.user))) / add_paper_conf.check_url_cnt * 100
            return JsonResponse({
                "state": "processUrlNext",
                "process-text": "Сверка с сайтами: " + f"{load_percent:.{1}f}%".format(
                    load_percent)
            })

        # если шилды для url не загружены
        if len(ShildFromURLText.objects.all().filter(url=url_to_process, author=request.user)) == 0:
            print("generate shilds")
            try:
                # если ссылка на википедию, то быстрее будет загружать текст статьи при помощи API
                if "wikipedia" in url_to_process.value:
                    # получаем название статьи
                    article_name = (url_to_process.value.split("/"))[-1].replace("_", " ")
                    # получаем текст статьи
                    text = wikipedia.page(article_name).summary
                else:
                    req = Request(url_to_process.value, headers={'User-Agent': "Magic Browser"})
                    text = text_from_html(urlopen(req, timeout=1).read())
                print(text)
                ShildFromURLText.objects.bulk_create(
                    [ShildFromURLText(**{'value': m, 'url': url_to_process, 'author': request.user}) for m in
                     get_shilds(text, start_time)])
                print("shilds generated")
            except:
                pass

        print("loop shilds")
        # перебираем шилды загруженного текста
        for found_shild in ShildFromURLText.objects.all().filter(url=url_to_process, author=request.user):
            #print(found_shild.value)
            # если превышено максимальное время выполнения скрипта
            if time.time() - start_time > MAX_SCRIPT_PROCESS_TIME:
                # рассчитываем процент загрузки
                load_percent = float(add_paper_conf.check_url_cnt - len(UrlToProcess.objects.all().filter(
                    author=request.user))) / add_paper_conf.check_url_cnt * 100
                return JsonResponse({
                    "state": "processUrlNext",
                    "process-text": "Сверка с сайтами: " + f"{load_percent:.{1}f}%".format(
                        load_percent)
                })
            try:
                # если шилд текста наден в проверяемом
                current_shild_to_process = ShildToProcess.objects.get(
                    author=request.user,
                    to_delete=False,
                    value=found_shild.value
                )
                # увеличиваем его счётчик на 1
                current_shild_to_process.founded_cnt = current_shild_to_process.founded_cnt + 1
                current_shild_to_process.save()
                print("shild found")
            except:
                pass
            found_shild.delete()
        url_to_process.delete()

    return JsonResponse({
        "state": "completeUrl",
        "process-text": "Сохранение результатов..."
    })


# обработка ссылок: сохранить статью
def save_paper(request, add_paper_conf):
    # кол-во шилдов, которые были найдены
    sum_u = 0
    # кол-во шилдов, которые встретились хотя бы в трёх различных источниках
    sum_t = 0
    # считаем кол-во встреченных и правдоподобных шилдов
    shilds = ShildToProcess.objects.all().filter(author=request.user, to_delete=False)
    for shild in shilds:
        if shild.founded_cnt > TRUTH_SHILD_CNT:
            sum_t = sum_t + 1
        if not shild.founded_cnt:
            sum_u = sum_u + 1

    # возвращаем уникальность и правдоподобность статьи
    u = float(sum_u) / len(shilds) * 100
    t = float(sum_t) / len(shilds) * 100

    # очищаем списки
    ShildToProcess.objects.all().filter(author=request.user).delete()
    UrlToProcess.objects.all().filter(author=request.user).delete()

    # создаём запись о статье
    Paper.objects.create(
        name=add_paper_conf.name,
        author=request.user,
        text=add_paper_conf.text,
        uniquenessPercent=u,
        truth=t
    )

    # очищаем параметры добаления статьи
    try:
        AddPaperConf.objects.get(author=request.user).delete()
    except:
        pass
    messages.info(request, "Оригинальность текста: " + f"{u:.{1}f}%".format(
        u) + ", правдоподобность: " + f"{t:.{1}f}%".format(t))
    return JsonResponse({"state": "ready", })
