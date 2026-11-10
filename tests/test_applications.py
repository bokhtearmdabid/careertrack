import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.applications.models import ApplicationNote, JobApplication
from apps.companies.models import Company

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="rahim", password="S3cure-pass-98")


@pytest.fixture
def other_user(db):
    return User.objects.create_user(username="karim", password="S3cure-pass-98")


@pytest.fixture
def auth_client(client, user):
    client.force_login(user)
    return client


def make_app(user, title="Python Developer", company_name="Acme Ltd", **kwargs):
    company, _ = Company.objects.get_or_create(name=company_name)
    return JobApplication.objects.create(
        user=user, company=company, job_title=title, **kwargs
    )


VALID_DATA = {
    "company_name": "Acme Ltd",
    "job_title": "Django Developer",
    "employment_type": "full_time",
    "application_date": "2026-01-15",
    "status": "applied",
}


def titles(response):
    return [a.job_title for a in response.context["applications"]]


# ---------- Authentication ----------

def test_list_requires_login(client, db):
    response = client.get(reverse("applications:list"))
    assert response.status_code == 302
    assert response.url.startswith(reverse("accounts:login"))


# ---------- Authorization (সবচেয়ে গুরুত্বপূর্ণ) ----------

def test_list_shows_only_own_applications(auth_client, user, other_user):
    make_app(user, "My Job")
    make_app(other_user, "Secret Job")
    response = auth_client.get(reverse("applications:list"))
    assert titles(response) == ["My Job"]


def test_cannot_view_others_application(auth_client, other_user):
    other = make_app(other_user)
    response = auth_client.get(reverse("applications:detail", args=[other.pk]))
    assert response.status_code == 404


def test_cannot_edit_others_application(auth_client, other_user):
    other = make_app(other_user, "Original")
    response = auth_client.post(
        reverse("applications:update", args=[other.pk]),
        {**VALID_DATA, "job_title": "Hacked"},
    )
    assert response.status_code == 404
    other.refresh_from_db()
    assert other.job_title == "Original"


def test_cannot_delete_others_application(auth_client, other_user):
    other = make_app(other_user)
    response = auth_client.post(reverse("applications:delete", args=[other.pk]))
    assert response.status_code == 404
    assert JobApplication.objects.filter(pk=other.pk).exists()


def test_cannot_add_note_to_others_application(auth_client, other_user):
    other = make_app(other_user)
    response = auth_client.post(
        reverse("applications:add_note", args=[other.pk]), {"content": "hi"}
    )
    assert response.status_code == 404
    assert ApplicationNote.objects.count() == 0


# ---------- Create / Update / Delete ----------

def test_create_assigns_logged_in_user(auth_client, user, other_user):
    # attacker অন্যের user id পাঠানোর চেষ্টা করলেও কাজ হবে না
    data = {**VALID_DATA, "user": other_user.pk}
    response = auth_client.post(reverse("applications:create"), data)
    assert response.status_code == 302
    assert JobApplication.objects.get().user == user


def test_create_reuses_existing_company_case_insensitive(auth_client):
    Company.objects.create(name="Acme Ltd")
    auth_client.post(
        reverse("applications:create"), {**VALID_DATA, "company_name": "acme ltd"}
    )
    assert Company.objects.count() == 1


def test_salary_validation_shows_form_error(auth_client):
    response = auth_client.post(
        reverse("applications:create"),
        {**VALID_DATA, "salary_min": 100000, "salary_max": 50000},
    )
    assert response.status_code == 200  # 500 নয়
    assert "salary_max" in response.context["form"].errors
    assert JobApplication.objects.count() == 0


def test_update_own_application(auth_client, user):
    app = make_app(user)
    response = auth_client.post(
        reverse("applications:update", args=[app.pk]),
        {**VALID_DATA, "job_title": "Updated", "status": "interview"},
    )
    assert response.status_code == 302
    app.refresh_from_db()
    assert app.job_title == "Updated"
    assert app.status == "interview"


def test_delete_own_application(auth_client, user):
    app = make_app(user)
    response = auth_client.post(reverse("applications:delete", args=[app.pk]))
    assert response.status_code == 302
    assert JobApplication.objects.count() == 0


def test_add_note_to_own_application(auth_client, user):
    app = make_app(user)
    auth_client.post(
        reverse("applications:add_note", args=[app.pk]), {"content": "Call HR"}
    )
    assert app.notes.get().content == "Call HR"


# ---------- Search, Filter, Sort, Pagination ----------

def test_search_by_title_and_company(auth_client, user):
    make_app(user, "Django Dev", "Acme")
    make_app(user, "Java Dev", "Globex")
    url = reverse("applications:list")
    assert titles(auth_client.get(url, {"q": "django"})) == ["Django Dev"]
    assert titles(auth_client.get(url, {"q": "globex"})) == ["Java Dev"]


def test_filter_by_status(auth_client, user):
    make_app(user, "A", status="applied")
    make_app(user, "B", status="interview")
    response = auth_client.get(reverse("applications:list"), {"status": "interview"})
    assert titles(response) == ["B"]


def test_sort_by_title(auth_client, user):
    make_app(user, "B Job")
    make_app(user, "A Job")
    response = auth_client.get(reverse("applications:list"), {"sort": "title"})
    assert titles(response) == ["A Job", "B Job"]


def test_invalid_sort_value_is_ignored(auth_client, user):
    make_app(user)
    response = auth_client.get(
        reverse("applications:list"), {"sort": "user__password"}
    )
    assert response.status_code == 200


def test_pagination(auth_client, user):
    for i in range(12):
        make_app(user, f"Job {i}")
    url = reverse("applications:list")
    assert len(auth_client.get(url).context["applications"]) == 10
    assert len(auth_client.get(url, {"page": 2}).context["applications"]) == 2