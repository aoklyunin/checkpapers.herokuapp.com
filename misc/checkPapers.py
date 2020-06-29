"""
    Возвращает процент уникальности в заданной статье
"""


def checkPapers(papaperA, paperB):
    return 100


def checkPaper(currentPaper, paperLst):
    minU = 100
    for paper in paperLst:
        u = checkPapers(currentPaper, paper.text)
        if u < minU:
            minU = u

    return minU
