from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Admin do Django
    path("admin/", admin.site.urls),

    # Login e Logout (Django nativo)
    path("login/", auth_views.LoginView.as_view(template_name="login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),

    # Rotas do app core
    path("", include("core.urls")),
]

