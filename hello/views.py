from django.shortcuts import render
from django.http import HttpResponse

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


# Create your views here.
def register(request):
    # return HttpResponse('Hello from Python!')
    return render(request, "register.html")


# Create your views here.
def login(request):
    # return HttpResponse('Hello from Python!')
    return render(request, "login.html")


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
