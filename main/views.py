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
def check(request):
    # return HttpResponse('Hello from Python!')
    return render(request, "check.html")


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
