from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView,
)

from .forms import ApplicationNoteForm, JobApplicationForm
from .models import JobApplication

# Whitelist: user শুধু এই key-গুলোই দিয়ে sort করতে পারবে
SORT_FIELDS = {
    "newest": "-application_date",
    "oldest": "application_date",
    "company": "company__name",
    "title": "job_title",
    "status": "status",
}
SORT_CHOICES = [
    ("newest", "Newest first"),
    ("oldest", "Oldest first"),
    ("company", "Company (A-Z)"),
    ("title", "Job title (A-Z)"),
    ("status", "Status"),
]


class OwnedApplicationMixin(LoginRequiredMixin):
    """Login লাগবে, আর শুধু নিজের application-ই পাওয়া যাবে।"""

    def get_queryset(self):
        return (
            JobApplication.objects
            .filter(user=self.request.user)
            .select_related("company")
        )


class JobApplicationListView(OwnedApplicationMixin, ListView):
    context_object_name = "applications"
    paginate_by = 10

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get("q", "").strip()
        status = self.request.GET.get("status", "")
        sort = self.request.GET.get("sort", "newest")

        if q:
            qs = qs.filter(Q(job_title__icontains=q) | Q(company__name__icontains=q))
        if status in JobApplication.Status.values:
            qs = qs.filter(status=status)
        if sort not in SORT_FIELDS:
            sort = "newest"
        # "-id" দিলে order সবসময় নির্দিষ্ট থাকে, নাহলে pagination-এ item ওলটপালট হতে পারে
        return qs.order_by(SORT_FIELDS[sort], "-id")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        params = self.request.GET.copy()
        params.pop("page", None)
        context.update({
            "q": self.request.GET.get("q", ""),
            "status": self.request.GET.get("status", ""),
            "sort": self.request.GET.get("sort", "newest"),
            "status_choices": JobApplication.Status.choices,
            "sort_choices": SORT_CHOICES,
            "querystring": params.urlencode(),  # pagination link-এ filter ধরে রাখতে
        })
        return context


class JobApplicationDetailView(OwnedApplicationMixin, DetailView):
    model = JobApplication

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["note_form"] = ApplicationNoteForm()
        return context


class JobApplicationCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = JobApplication
    form_class = JobApplicationForm
    success_url = reverse_lazy("applications:list")
    success_message = "Application added."

    def form_valid(self, form):
        form.instance.user = self.request.user  # user সবসময় logged-in user
        return super().form_valid(form)


class JobApplicationUpdateView(OwnedApplicationMixin, SuccessMessageMixin, UpdateView):
    form_class = JobApplicationForm
    success_message = "Application updated."

    def get_success_url(self):
        return reverse("applications:detail", args=[self.object.pk])


class JobApplicationDeleteView(OwnedApplicationMixin, SuccessMessageMixin, DeleteView):
    success_url = reverse_lazy("applications:list")
    success_message = "Application deleted."


@login_required
@require_POST
def add_note(request, pk):
    application = get_object_or_404(JobApplication, pk=pk, user=request.user)
    form = ApplicationNoteForm(request.POST)
    if form.is_valid():
        note = form.save(commit=False)
        note.application = application
        note.save()
        messages.success(request, "Note added.")
    else:
        messages.error(request, "Note cannot be empty.")
    return redirect("applications:detail", pk=pk)