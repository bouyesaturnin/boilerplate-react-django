from django.urls import path
from . import views

urlpatterns = [
    path("register/", views.register, name="auth-register"),
    path("login/", views.LoginView.as_view(), name="auth-login"),
    path("token/refresh/", views.RefreshView.as_view(), name="auth-token-refresh"),
    path("logout/", views.logout, name="auth-logout"),
    path("me/", views.me, name="auth-me"),
]
