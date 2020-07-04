# -*- coding: utf-8 -*-
"""
    Возвращает процент уникальности в заданной статье
"""
import os
import re
import time
from urllib.parse import urlencode
from urllib.request import urlopen, Request
from bs4.element import Comment
import numpy
import yandex_search
from bs4 import BeautifulSoup
from selenium import webdriver
from wikipedia import wikipedia
from django.db import connection

from main.models import Paper

SHILD_LENGTH = 5


def tag_visible(element):
    if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
        return False
    if isinstance(element, Comment):
        return False
    return True


def text_from_html(body):
    soup = BeautifulSoup(body, 'html.parser')
    texts = soup.findAll(text=True)
    visible_texts = filter(tag_visible, texts)
    return u" ".join(t.strip() for t in visible_texts)


def getShilds(text, shildLength):
    text.replace("\n", " ")
    textWithSpaces = re.sub(r'[^A-zА-я0-9 ]', '', text)
    textWithOneSpace = re.sub(r'\s+', ' ', textWithSpaces)
    words = textWithOneSpace.split(" ")
    shilds = []
    for i in range(len(words) - shildLength):
        shild = " ".join(words[i:i + shildLength])
        shilds.append(shild)
    return shilds


def checkPaper(currentPaperShilds, urlList):
    findShildCnt = numpy.zeros(len(currentPaperShilds))
    startTime = time.time()
    for url in urlList:
        print(url)
        deltaTime = time.time() - startTime
        # print(str(round(deltaTime / 60)) + " " + url)
        if deltaTime > 60 * 2:
            break
        try:
            if "wikipedia" in url:
                articleName = (url.split("/"))[-1].replace("_", " ")
                text = wikipedia.page(articleName).summary
                # print(">"+text)
            else:
                req = Request(url, headers={'User-Agent': "Magic Browser"})
                text = text_from_html(urlopen(req, timeout=1).read())

            for foundedShild in getShilds(text, SHILD_LENGTH):
                if foundedShild in currentPaperShilds:
                    index = currentPaperShilds.index(foundedShild)
                    findShildCnt[index] = findShildCnt[index] + 1
        except:
            pass
            print("error loading page: " + url)

    sumU = 0
    sumT = 0
    # print("non finded shilds:")
    for i in range(len(findShildCnt)):
        print(currentPaperShilds[i] + " " + str(findShildCnt[i]))
        if findShildCnt[i] > 3:
            sumT = sumT + 1
        if findShildCnt[i]:
            sumU = sumU + 1
        # else:

    print([sumU, sumT, len(findShildCnt)])
    return [(1 - float(sumU) / len(findShildCnt)) * 100, float(sumT) / len(findShildCnt) * 100]


def load_urls(shilds):
    options = webdriver.ChromeOptions()
    # options.add_argument('headless')
    # options.add_argument('window-size=1920x1080')
    # options.add_argument("disable-gpu")
    driver = webdriver.Chrome(str(os.environ.get('CHROMEDRIVER_PATH')), options=options)

    url = "http://yandex.ru/search"

    urls = set()
    for shild in shilds:
        print(shild)
        query = urlencode({'text': '"' + shild + '"'})
        # print(url + query)
        # request = Request(url + '?' + query, None, headers)
        driver.get(url + '?' + query)
        localUrlsSet = set()
        for link in driver.find_elements_by_xpath('//a'):
            strLink = str(link.get_attribute("href"))
            if (not "yandex" in strLink) and (not "bing" in strLink) and (not "google" in strLink) and (
                    not "mail" in strLink) and (strLink is not None):
                localUrlsSet.add(strLink)
        if len(localUrlsSet) == 0:
            return urls
        else:
            urls.update(localUrlsSet)
    print("ready")
    return urls


def createPaper(text, name, author):
    print("create paper")
    shilds = getShilds(text, SHILD_LENGTH)
    print("geted shilds")
    urls = load_urls(shilds)
    if len(urls) == 0:
        return [-1, 0]
    [u, t] = checkPaper(shilds, urls)
    # из-за долгого времени ожидания соединение обрывается
    # нужно его перезапускать
    connection.connect()
    Paper.objects.create(
        name=name,
        author=author,
        text=text,
        uniquenessPercent=u,
        truth=t
    )
    return [u, t]


def createPaperYandex(text, name, author):
    [u, t] = checkPaperYandex(text)
    if (u == -1):
        return [u, t]
    # из-за долгого времени ожидания соединение обрывается
    # нужно его перезапускать
    connection.connect()
    Paper.objects.create(
        name=name,
        author=author,
        text=text,
        uniquenessPercent=u,
        truth=t
    )
    return [u, t]


def checkPaperYandex(currentPaper):
    print(currentPaper)
    currentPaperShilds = getShilds(currentPaper, SHILD_LENGTH)
    if len(currentPaperShilds) == 0:
        return 0
    yandex = yandex_search.Yandex(api_user='aoklyunin', api_key='03.210671841:b75fddc50ebc4d5938fc5c192bd47964')
    urlList = set()
    for shild in currentPaperShilds:
        # print(shild)
        try:
            searchUrls = [str(result["url"]) for result in yandex.search('"' + shild + '"').items[:10]]
            # print(searchUrls)
            urlList.update(searchUrls)
        except yandex_search.ConfigException:
            print("error search: указан неверный ip адрес ")
            return [-1, 0]
            # pass
    # print(urlList)
    return checkPaper(currentPaperShilds, urlList)
