from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import ProfileForm, RegisterForm, UserUpdateForm
from .models import UserProfile


def home(request):
    context = {"app_name": "CareerTrack"}
    return render(request, "home.html", context)


def register(request):
    if request.user.is_authenticated:
        return redirect("accounts:profile")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Account created successfully.")
            return redirect("accounts:profile")
    else:
        form = RegisterForm()
    return render(request, "accounts/register.html", {"form": form})


@login_required
def profile(request):
    profile_obj, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileForm(request.POST, instance=profile_obj)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Profile updated.")
            return redirect("accounts:profile")
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileForm(instance=profile_obj)

    return render(
        request,
        "accounts/profile.html",
        {"user_form": user_form, "profile_form": profile_form},
    )