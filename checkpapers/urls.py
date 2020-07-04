# -*- coding: utf-8 -*-
from django.urls import path
import main.views
import main.auth
from django.contrib import admin

admin.autodiscover()

urlpatterns = [
    path("", main.views.index, name="index"),
    path("check", main.views.check, name="check"),
    path("login", main.auth.login, name="login"),
    path("logout", main.auth.logout_view, name="logout_view"),
    path("register", main.auth.register, name="register"),
    path("about", main.views.about, name="about"),
    path("personal", main.views.personal_firs_page, name="personalFirsPage"),
    path("personal/<int:page>", main.views.personal, name="personal"),
    path("papers", main.views.papers_first_page, name="papers_first_page"),
    path("read_paper/<int:paper_id>", main.views.read_paper, name="readPaper"),
    path("papers/<int:page>", main.views.papers, name="papers"),
    path("need_login", main.views.need_login, name="need_login"),
    path("load_urls", main.views.load_urls, name="load_urls"),
    path("process_urls", main.views.process_urls, name="process_urls"),
    path("delete_paper/<int:paper_id>", main.views.delete_paper, name="delete_paper"),
    path("admin/", admin.site.urls),
]
