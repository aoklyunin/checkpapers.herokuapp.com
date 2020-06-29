# -*- coding: utf-8 -*-
from django.contrib import auth
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as dj_login

from hello.forms import RegisterForm, LoginForm


# метод регистрации
def register(request):
    # если post запрос
    if request.method == 'POST':
        # строим форму на основе запроса
        form = RegisterForm(request.POST)
        # если форма заполнена корректно
        if form.is_valid():
            # проверяем, что пароли совпадают
            if form.cleaned_data["password"] != form.cleaned_data["rep_password"]:
                # выводим сообщение и перезаполняем форму
                messages.error(request, "пароли не совпадают")
                data = {'username': form.cleaned_data["username"],
                        'mail': form.cleaned_data["mail"],
                        }
                # перерисовываем окно
                return render(request, "register.html", {
                    'form': RegisterForm(initial=data),
                    'ins_form': LoginForm()
                })
            else:
                # получаем данные из формы
                musername = form.cleaned_data["username"]
                mmail = form.cleaned_data["mail"]
                mpassword = form.cleaned_data["password"]
                try:
                    # создаём пользователя
                    user = User.objects.create_user(username=musername,
                                                    email=mmail,
                                                    password=mpassword)
                    # если получилось создать пользователя
                    if user:
                        dj_login(request, user)
                        return HttpResponseRedirect("personal")

                except:
                    # если не получилось создать пользователя, то выводим сообщение
                    messages.error(request, "Такой пользователь уже есть")
                    # заполняем дату формы
                    data = {'username': form.cleaned_data["username"],
                            'mail': form.cleaned_data["mail"],
                            }
                    # рисуем окно регистрации
                    return render(request, "register.html", {
                        'form': RegisterForm(initial=data),
                        'ins_form': LoginForm()
                    })
        else:
            # перезагружаем страницу
            messages.error(request, "форма не правильная")
            return HttpResponseRedirect("register")
    else:
        # возвращаем простое окно регистрации
        return render(request, "register.html", {
            'form': RegisterForm()
        })


# выход из системы
def logout_view(request):
    logout(request)
    return HttpResponseRedirect("login")


# стартовая страница
def login(request):
    # print("login")
    # обработка входа
    if request.method == "POST":
        # print("post "+str(request))
        # если в post-запросе есть поля логина/пароля
        if ("username" in request.POST) and ("password" in request.POST):
            username = request.POST['username']
            password = request.POST['password']

            # пробуем залогиниться
            user = auth.authenticate(username=username, password=password)
            request.POST._mutable = True
            # если полльзователь существует и он активен
            if user is not None and user.is_active:
                # входим на сайт
                auth.login(request, user)
                # выводим сообщение об удаче
                messages.success(request, "успешный вход")
                return HttpResponseRedirect("personal")
            else:
                messages.error(request, "пара логин-пароль не найдена")

    template = 'login.html'
    context = {
        "user": request.user,
        "login_form": LoginForm(),
    }
    return render(request, template, context)
