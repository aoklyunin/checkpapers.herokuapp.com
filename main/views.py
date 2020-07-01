from django.contrib import auth, messages
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import login as auth_login

from main.forms import PaperForm
from misc.checkPapers import checkPaper
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
    # если post запрос
    if request.method == 'POST':
        # строим форму на основе запроса
        form = PaperForm(request.POST)
        # если форма заполнена корректно
        if form.is_valid():
            data = {'text': form.cleaned_data["text"]
                    }
            # проверяем, что пароли совпадают
            if form.cleaned_data["text"] == "":
                # выводим сообщение и перезаполняем форму
                messages.error(request, "Вы послали на проверку пустую статью")

            else:
                papers = Paper.objects.all()
                u = checkPaper(form.cleaned_data["text"], papers)
                Paper.objects.create(
                    author=request.user,
                    text=form.cleaned_data["text"],
                    uniquenessPercent=u
                )
            messages.info(request, "Уникальность текста: " + f"{u:.{1}f}%".format(u))
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


# Create your views here.
def personal(request):
    # return HttpResponse('Hello from Python!')
    if request.user.is_authenticated:
        papers = Paper.objects.all().filter(author=request.user)
        return render(request, "personal.html", {
            "papers": papers,
            "paperCount": len(papers)
        })
    else:
        return render(request, "personal.html", {
            "papers": [],
            "paperCount": 0
        })


def deletePaper(request, paper_id):
    # return HttpResponse('Hello from Python!')
    if not request.user.is_authenticated:
        messages.error(request, "статьи может удалять только авторизованный пользователь")
        return HttpResponseRedirect("/login")

    try:
        paper = Paper.objects.get(pk=paper_id)
        if not request.user == paper.author:
            messages.error(request, "Вы не можете удалять чужые статьи")
        else:
            paper.delete()
    except:
        messages.error(request, "статья с id "+str(paper_id)+" не найдена")

    return HttpResponseRedirect("/personal")

