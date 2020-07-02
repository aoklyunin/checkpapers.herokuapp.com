# -*- coding: utf-8 -*-
from django.contrib import auth, messages
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm
from django.core import paginator
from django.core.paginator import PageNotAnInteger, EmptyPage, Paginator
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import login as auth_login

from main.forms import PaperForm
from misc.checkPapers import checkPaper, createPaper
from .models import Greeting, Paper


# Create your views here.
def index(request):
    # return HttpResponse('Hello from Python!')
    return render(request, "index.html")


# Create your views here.
def test(request):
    # return HttpResponse('Hello from Python!')
    return render(request, "testPage.html")


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
                [u, t] = createPaper(form.cleaned_data["text"], form.cleaned_data["name"], request.user)
                messages.info(request, "Уникальность текста: " + f"{u:.{1}f}%".format(
                    u) + ", правдивость: " + f"{u:.{1}f}%".format(t))
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
        paginator = Paginator(Paper.objects.all().filter(author=request.user), 12)
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
        paginator = Paginator(Paper.objects.all(), 12)
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
