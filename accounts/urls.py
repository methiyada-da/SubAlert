from django.contrib.auth.views import LogoutView
from django.urls import path

from .views import AccountLoginView, RegisterView


app_name = "accounts"

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", AccountLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
]
