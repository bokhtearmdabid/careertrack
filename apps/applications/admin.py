from django.contrib import admin
from .models import ApplicationNote, JobApplication


class ApplicationNoteInline(admin.TabularInline):
    model = ApplicationNote
    extra = 0


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ("job_title", "company", "user", "status", "application_date")
    list_filter = ("status", "employment_type")
    search_fields = ("job_title", "company__name")
    inlines = [ApplicationNoteInline]