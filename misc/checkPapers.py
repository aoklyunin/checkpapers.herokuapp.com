"""
    Возвращает процент уникальности в заданной статье
"""
import re

import numpy

from main.models import Paper


def createPaper(text, author):
    u = checkPaper(text, Paper.objects.all())
    Paper.objects.create(
        author=author,
        text=text,
        uniquenessPercent=u,
        shilds=";".join(getShilds(text, 3))
    )
    return u


def getShilds(text, shildLength):
    textWithSpaces = re.sub(r'[^A-zА-я0-9 ]', '', text)
    textWithOneSpace = re.sub(r'\s+', ' ', textWithSpaces)
    words = textWithOneSpace.split(" ")
    shilds = []
    for i in range(len(words) - shildLength):
        shild = " ".join(words[i:i + shildLength])
        shilds.append(shild)
    return shilds


def checkPaper(currentPaper, paperLst):
    currentPaperShilds = getShilds(currentPaper, 3)
    if len(currentPaperShilds) == 0:
        return 0
    flgFindShild = numpy.zeros(len(currentPaperShilds))
    # print(currentPaperShilds)
    for paper in paperLst:
        for shild in paper.shilds.split(";"):
            # print(shild)
            if shild in currentPaperShilds:
                flgFindShild[currentPaperShilds.index(shild)] = True

    sum = 0
    for i in range(len(flgFindShild)):
        if flgFindShild[i]:
            sum = sum + 1
        # else:
        # print(currentPaperShilds[i])
    return (1 - float(sum) / len(flgFindShild)) * 100
