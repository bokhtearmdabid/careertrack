import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError

from apps.applications.models import JobApplication
from apps.companies.models import Company

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="rahim", password="pass12345")


@pytest.fixture
def company(db):
    return Company.objects.create(name="Acme Ltd")


def test_default_status_is_applied(user, company):
    app = JobApplication.objects.create(
        user=user, company=company, job_title="Python Developer"
    )
    assert app.status == JobApplication.Status.APPLIED


def test_str_representation(user, company):
    app = JobApplication.objects.create(
        user=user, company=company, job_title="Python Developer"
    )
    assert str(app) == "Python Developer at Acme Ltd"


def test_salary_max_cannot_be_less_than_min(user, company):
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            JobApplication.objects.create(
                user=user,
                company=company,
                job_title="Dev",
                salary_min=100000,
                salary_max=50000,
            )


def test_company_with_applications_cannot_be_deleted(user, company):
    JobApplication.objects.create(user=user, company=company, job_title="Dev")
    with pytest.raises(ProtectedError):
        company.delete()


def test_deleting_user_deletes_their_applications(user, company):
    JobApplication.objects.create(user=user, company=company, job_title="Dev")
    user.delete()
    assert JobApplication.objects.count() == 0