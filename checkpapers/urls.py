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
    path("personal", main.views.personalFirsPage, name="personalFirsPage"),
    path("personal/<int:page>", main.views.personal, name="personal"),
    path("papers", main.views.papersFirsPage, name="papersFirsPage"),
    path("readpaper/<int:paper_id>", main.views.readPaper, name="readPaper"),
    path("papers/<int:page>", main.views.papers, name="papers"),
    path("needlogin", main.views.needLogin, name="needlogin"),
    path("deletepaper/<int:paper_id>", main.views.deletePaper, name="deletepaper"),
    path("admin/", admin.site.urls),
]
