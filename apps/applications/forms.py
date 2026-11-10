from django import forms

from apps.companies.models import Company

from .models import ApplicationNote, JobApplication


class JobApplicationForm(forms.ModelForm):
    # Model-এর field নয়, user এখানে company-র নাম লিখবে
    company_name = forms.CharField(max_length=200, label="Company")

    field_order = [
        "company_name", "job_title", "job_description", "salary_min",
        "salary_max", "location", "employment_type", "application_date",
        "status", "job_url",
    ]

    class Meta:
        model = JobApplication
        fields = (
            "job_title", "job_description", "salary_min", "salary_max",
            "location", "employment_type", "application_date", "status",
            "job_url",
        )
        widgets = {
            "job_description": forms.Textarea(attrs={"rows": 5}),
            "application_date": forms.DateInput(
                attrs={"type": "date"}, format="%Y-%m-%d"
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Edit করার সময় আগের company-র নাম দেখাও
        if self.instance.pk:
            self.fields["company_name"].initial = self.instance.company.name
        # Bootstrap styling
        for field in self.fields.values():
            css = "form-select" if isinstance(field.widget, forms.Select) else "form-control"
            field.widget.attrs["class"] = css

    def clean(self):
        cleaned = super().clean()
        salary_min = cleaned.get("salary_min")
        salary_max = cleaned.get("salary_max")
        if salary_min is not None and salary_max is not None and salary_max < salary_min:
            self.add_error("salary_max", "Maximum salary cannot be less than minimum salary.")
        return cleaned

    def save(self, commit=True):
        name = self.cleaned_data["company_name"]
        company = Company.objects.filter(name__iexact=name).first()
        if company is None:
            company = Company.objects.create(name=name)
        self.instance.company = company
        return super().save(commit=commit)


class ApplicationNoteForm(forms.ModelForm):
    class Meta:
        model = ApplicationNote
        fields = ("content",)
        widgets = {
            "content": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
        }