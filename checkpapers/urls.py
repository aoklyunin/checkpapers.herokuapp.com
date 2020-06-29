from django.urls import path, include

from django.contrib import admin

admin.autodiscover()

import hello.views
import hello.auth

# To add a new path, first import the app:
# import blog
#
# Then add the new path:
# path('blog/', blog.urls, name="blog")
#
# Learn more here: https://docs.djangoproject.com/en/2.1/topics/http/urls/

urlpatterns = [
    path("", hello.views.index, name="index"),
    path("test", hello.views.test, name="test"),
    path("upload", hello.views.upload, name="upload"),
    path("login", hello.auth.login, name="login"),
    path("logout", hello.auth.logout_view, name="logout_view"),
    path("register", hello.auth.register, name="register"),
    path("about", hello.views.about, name="about"),
    path("personal", hello.views.personal, name="personal"),
    path("db/", hello.views.db, name="db"),
    path("admin/", admin.site.urls),
]
