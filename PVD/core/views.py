from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect


@login_required
def dashboard(request):
    # Admin vai para tela admin; demais para tela comum
    if request.user.is_staff:
        return render(request, "home_admin.html")
    return render(request, "home.html")


def cadastro(request):
    # Cadastro simples usando o formulário padrão do Django
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("login")
    else:
        form = UserCreationForm()

    return render(request, "cadastro.html", {"form": form})

