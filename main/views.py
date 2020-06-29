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
            messages.info(request, "Уникальность текста: "+f"{u:.{1}f}%".format(u))
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
    return render(request, "personal.html")


def db(request):
    greeting = Greeting()
    greeting.save()

    greetings = Greeting.objects.all()

    return render(request, "db.html", {"greetings": greetings})
