from django.urls import path

from . import views

app_name = "applications"

urlpatterns = [
    path("", views.JobApplicationListView.as_view(), name="list"),
    path("new/", views.JobApplicationCreateView.as_view(), name="create"),
    path("<int:pk>/", views.JobApplicationDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.JobApplicationUpdateView.as_view(), name="update"),
    path("<int:pk>/delete/", views.JobApplicationDeleteView.as_view(), name="delete"),
    path("<int:pk>/notes/add/", views.add_note, name="add_note"),
]