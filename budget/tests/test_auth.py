import pytest
from django.urls import reverse
from django.contrib.auth.models import User

@pytest.mark.django_db
def test_login_logout(client):
    User.objects.create_user(username="testuser", password="pass")
    login = client.login(username="testuser", password="pass")
    assert login
    response = client.post(reverse("logout"))
    assert response.status_code in (200, 302)
