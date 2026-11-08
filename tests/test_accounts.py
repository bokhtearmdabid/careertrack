import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="rahim", email="rahim@example.com", password="S3cure-pass-98"
    )


def test_register_creates_user_and_profile(client, db):
    response = client.post(
        reverse("accounts:register"),
        {
            "username": "karim",
            "email": "karim@example.com",
            "password1": "S3cure-pass-98",
            "password2": "S3cure-pass-98",
        },
    )
    assert response.status_code == 302
    karim = User.objects.get(username="karim")
    assert karim.profile is not None


def test_register_rejects_mismatched_passwords(client, db):
    response = client.post(
        reverse("accounts:register"),
        {
            "username": "karim",
            "email": "karim@example.com",
            "password1": "S3cure-pass-98",
            "password2": "different-pass-11",
        },
    )
    assert response.status_code == 200
    assert not User.objects.filter(username="karim").exists()


def test_password_is_hashed(user):
    assert user.password != "S3cure-pass-98"
    assert user.password.startswith("pbkdf2_sha256$")


def test_login_works(client, user):
    response = client.post(
        reverse("accounts:login"),
        {"username": "rahim", "password": "S3cure-pass-98"},
    )
    assert response.status_code == 302


def test_profile_requires_login(client, db):
    response = client.get(reverse("accounts:profile"))
    assert response.status_code == 302
    assert response.url.startswith(reverse("accounts:login"))


def test_logged_in_user_can_update_profile(client, user):
    client.force_login(user)
    response = client.post(
        reverse("accounts:profile"),
        {"first_name": "Rahim", "last_name": "Uddin",
         "email": "rahim@example.com", "phone": "01700000000", "bio": "Dev"},
    )
    assert response.status_code == 302
    user.refresh_from_db()
    assert user.first_name == "Rahim"
    assert user.profile.phone == "01700000000"


def test_password_reset_sends_email(client, user, mailoutbox):
    client.post(reverse("accounts:password_reset"), {"email": "rahim@example.com"})
    assert len(mailoutbox) == 1