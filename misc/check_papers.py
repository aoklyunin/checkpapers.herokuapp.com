# -*- coding: utf-8 -*-
import re
import time
from urllib.request import urlopen, Request
from bs4.element import Comment
import numpy
import yandex_search
from bs4 import BeautifulSoup
from wikipedia import wikipedia
from main.models import Paper
from django.db import connection

# размер шилда
SHILD_LENGTH = 5
# кол-во источников, в которых встретился шилд, чтобы можно было считать шилд правдоподобным
TRUTH_SHILD_CNT = 3
# максимальное время выполнения скрипта у heroku ограничение на время ответа 30, берём с запасом 20
MAX_SCRIPT_PROCESS_TIME = 20


# фильтр видимых html тэгов
def tag_visible(element):
    if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
        return False
    if isinstance(element, Comment):
        return False
    return True


# получить текест из html
def text_from_html(body):
    soup = BeautifulSoup(body, 'html.parser')
    texts = soup.findAll(text=True)
    visible_texts = filter(tag_visible, texts)
    return u" ".join(t.strip() for t in visible_texts)


# получить список шилдов из текста
def get_shilds(text, start_time):
    text.replace("\n", " ")
    text_with_spaces = re.sub(r'[^A-zА-я0-9 ]', '', text)
    text_with_one_space = re.sub(r'\s+', ' ', text_with_spaces)
    words = text_with_one_space.split(" ")
    shilds = []
    for i in range(len(words) - SHILD_LENGTH):
        # если превышено максимальное время выполнения скрипта
        if time.time() - start_time > MAX_SCRIPT_PROCESS_TIME:
            break
        shild = " ".join(words[i:i + SHILD_LENGTH])
        shilds.append(shild)
    return shilds


# проверить статью
def check_paper(current_paper_shilds, url_list):
    # массив счётчиков, в скольких статьях найден тот или иной шилд
    find_shild_cnt = numpy.zeros(len(current_paper_shilds))
    # время начала проверки
    start_time = time.time()

    # из-за долгого времени ожидания соединение обрывается
    # нужно его перезапускать
    connection.connect()
    # сначала перебираем статьи на сайте(это быстрее)
    for paper in Paper.objects.all():
        # если с начала обработки прошёл час
        if time.time() - start_time > 60 * 60:
            # прерываем цикл
            break
        for foundedShild in get_shilds(paper.text, time.time()):
            if foundedShild in current_paper_shilds:
                index = current_paper_shilds.index(foundedShild)
                find_shild_cnt[index] = find_shild_cnt[index] + 1

    # перебираем статьи по ссылкам на другие сайты
    for url in url_list:
        # если с начала обработки прошёл час
        if time.time() - start_time > 60 * 60:
            # прерываем цикл
            break
        try:
            # если ссылка на википедию, то быстрее будет загружать текст статьи при помощи API
            if "wikipedia" in url:
                # получаем название статьи
                article_name = (url.split("/"))[-1].replace("_", " ")
                # получаем текст статьи
                text = wikipedia.page(article_name).summary
            else:
                # загружаем видимый текст со страницы
                req = Request(url, headers={'User-Agent': "Magic Browser"})
                text = text_from_html(urlopen(req, timeout=3).read())
            # перебираем шилды текста с которым сравниваем
            for foundedShild in get_shilds(text, time.time()):
                # если в проверяемой статье есть такой шилд, то увеличиваем
                # соответствующий элемент массива счётчиков
                if foundedShild in current_paper_shilds:
                    index = current_paper_shilds.index(foundedShild)
                    find_shild_cnt[index] = find_shild_cnt[index] + 1
        except:
            pass
            print("error loading page: " + url)
    # кол-во шилдов, которые были найдены
    sum_u = 0
    # кол-во шилдов, которые встретились хотя бы в трёх различных источниках
    sum_t = 0
    # считаем кол-во встреченных и правдоподобных шилдов
    for i in range(len(find_shild_cnt)):
        if find_shild_cnt[i] > TRUTH_SHILD_CNT:
            sum_t = sum_t + 1
        if not find_shild_cnt[i]:
            sum_u = sum_u + 1

    # возвращаем уникальность и правдоподобность статьи
    return [float(sum_u) / len(find_shild_cnt) * 100, float(sum_t) / len(find_shild_cnt) * 100]


# проверить статью с помощью API яндекса
def check_paper_with_yandex_api(current_paper):
    # получаем шилды программы
    current_paper_shilds = get_shilds(current_paper, time.time())
    # подключаем API яндекса
    yandex = yandex_search.Yandex(api_user='aoklyunin', api_key='03.210671841:b75fddc50ebc4d5938fc5c192bd47964')
    # создаём множество ссылок
    url_list = set()
    # по каждому из шилдов получаем список ссылок на страницы, в которых он найден
    for shild in current_paper_shilds:
        try:
            search_urls = [str(result["url"]) for result in yandex.search('"' + shild + '"').items[:10]]
            url_list.update(search_urls)
            # у API есть ограничение на кол-во запросов в секунду, поэтому добавляем небольшую задержку
            time.sleep(0.05)
        except yandex_search.ConfigException:
            print("error search: используется ip адрес, не совпадающий с указанным в яндекс XML")
            return [-1, 0]

    return check_paper(current_paper_shilds, url_list)
