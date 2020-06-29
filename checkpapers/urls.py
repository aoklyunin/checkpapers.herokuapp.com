from django.urls import path, include

from django.contrib import admin

admin.autodiscover()

import main.views
import main.auth

# To add a new path, first import the app:
# import blog
#
# Then add the new path:
# path('blog/', blog.urls, name="blog")
#
# Learn more here: https://docs.djangoproject.com/en/2.1/topics/http/urls/

urlpatterns = [
    path("", main.views.index, name="index"),
    path("test", main.views.test, name="test"),
    path("upload", main.views.upload, name="upload"),
    path("login", main.auth.login, name="login"),
    path("logout", main.auth.logout_view, name="logout_view"),
    path("register", main.auth.register, name="register"),
    path("about", main.views.about, name="about"),
    path("personal", main.views.personal, name="personal"),
    path("db/", main.views.db, name="db"),
    path("admin/", admin.site.urls),
]
