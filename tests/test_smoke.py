import pytest
from django.test import Client


@pytest.mark.django_db
def test_homepage():
    client = Client()
    from django.contrib.auth import get_user_model

    user = get_user_model().objects.create_user(username="smoke", password="password123")
    client.force_login(user)
    response = client.get("/")
    assert response.status_code == 200
    assert "Dashboard" in response.content.decode("utf-8")
