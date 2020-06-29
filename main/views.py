from django.contrib import auth
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import login as auth_login

from .models import Greeting


# Create your views here.
def index(request):
    # return HttpResponse('Hello from Python!')
    return render(request, "index.html")


# Create your views here.
def test(request):
    # return HttpResponse('Hello from Python!')
    return render(request, "testPage.html")


# Create your views here.
def upload(request):
    # return HttpResponse('Hello from Python!')
    return render(request, "upload.html")


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
        username = form.cleaned_data.get('username')
        my_password = form.cleaned_data.get('password1')
        user = authenticate(username=username, password=my_password)
        auth_login(request, user)
        return redirect('personal')
    else:
        form = UserCreationForm()
        return render(request, 'register.html', {'form': form})


# Create your views here.
def login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = auth.authenticate(username=username, password=password)
        if user is not None and user.is_active:
            # Правильный пароль и пользователь "активен"
            auth.login(request, user)
            # Перенаправление на "правильную" страницу
            return redirect('personal')
        else:
            # Отображение страницы с ошибкой
            return redirect('personal')

    else:
        # return HttpResponse('Hello from Python!')
        return render(request, "login.html")


def logout(request):
    auth.logout(request)
    # Перенаправление на страницу.
    return HttpResponseRedirect("/account/loggedout/")


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
