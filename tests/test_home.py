from django.urls import reverse


def test_home_page_loads(client):
    response = client.get(reverse("accounts:home"))
    assert response.status_code == 200
    assert b"CareerTrack" in response.content