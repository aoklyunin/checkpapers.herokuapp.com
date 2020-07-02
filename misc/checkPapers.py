"""
    Возвращает процент уникальности в заданной статье
"""
import re
import time
from urllib.request import urlopen, Request
from bs4.element import Comment
import numpy
import yandex_search
from bs4 import BeautifulSoup
from wikipedia import wikipedia

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


def getShildsFromPaper(paper):
    return paper.shilds


def createPaper(text, name, author):
    [u, t] = checkPaper(text)
    Paper.objects.create(
        name=name,
        author=author,
        text=text,
        uniquenessPercent=u,
        truth=t
    )
    return [u, t]


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


def checkPaper(currentPaper):
    print(currentPaper)
    currentPaperShilds = getShilds(currentPaper, SHILD_LENGTH)
    if len(currentPaperShilds) == 0:
        return 0
    findShildCnt = numpy.zeros(len(currentPaperShilds))
    yandex = yandex_search.Yandex(api_user='aoklyunin', api_key='03.210671841:b75fddc50ebc4d5938fc5c192bd47964')

    startTime = time.time()
    urlList = set()
    for shild in currentPaperShilds:
        try:
            urlList.update([str(result["url"]) for result in yandex.search('"' + shild + '"').items[:10]])
        except:
            pass
    print(urlList)
    for url in urlList:
        deltaTime = time.time() - startTime
        print(str(round(deltaTime / 60)) + " " + url)
        if (deltaTime > 60 * 5):
            break
        if "youtube" in url:
            continue
        try:
            if "wikipedia" in url:
                articleName = (url.split("/"))[-1].replace("_", " ")
                text = wikipedia.page(articleName).summary
                # print(">"+text)
            else:
                req = Request(url, headers={'User-Agent': "Magic Browser"})
                text = text_from_html(urlopen(req).read())
            for findedshild in getShilds(text, SHILD_LENGTH):
                if findedshild in currentPaperShilds:
                    index = currentPaperShilds.index(findedshild)
                    findShildCnt[index] = findShildCnt[index] + 1
        except:
            pass
            print("error loading page: " + url)

    sumU = 0
    sumT = 0
    # print("non finded shilds:")
    for i in range(len(findShildCnt)):
        print(currentPaperShilds+" "+str(findShildCnt[i]))
        if findShildCnt[i] > 3:
            sumT = sumT + 1
        if findShildCnt[i]:
            sumU = sumU + 1
        # else:
        # print(currentPaperShilds[i])
    return [(1 - float(sumU) / len(findShildCnt)) * 100, float(sumT) / len(findShildCnt) * 100]
