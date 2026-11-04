from django.shortcuts import render


def home(request):
    context = {"app_name": "CareerTrack"}
    return render(request, "home.html", context)
