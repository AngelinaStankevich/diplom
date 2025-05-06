import pytest
from django.urls import reverse
from django.contrib.auth.models import User

@pytest.mark.django_db
def test_dashboard_view(client):
    user = User.objects.create_user(username="testuser", password="pass")
    client.login(username="testuser", password="pass")
    response = client.get(reverse("dashboard"))
    assert response.status_code == 200
    content = response.content.decode('utf-8')
    assert "Главная" in content or "Обзор" in content

@pytest.mark.django_db
def test_transaction_create_view(client):
    user = User.objects.create_user(username="testuser", password="pass")
    client.login(username="testuser", password="pass")
    url = reverse("transaction_create")
    response = client.get(url)
    assert response.status_code == 200
    # Проверка наличия формы
    assert b"form" in response.content
