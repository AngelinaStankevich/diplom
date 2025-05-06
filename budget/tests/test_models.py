import pytest
from budget.models import Category, Currency, Transaction, Budget
from django.contrib.auth.models import User
from datetime import date

@pytest.mark.django_db
def test_create_category():
    user = User.objects.create_user(username="testuser", password="pass")
    cat = Category.objects.create(name="Еда", is_income=False, color="#ff0000", user=user)
    assert cat.name == "Еда"
    assert not cat.is_income

@pytest.mark.django_db
def test_currency_str():
    cur = Currency.objects.create(code="USD", name="Доллар", rate=3.2)
    assert str(cur) == "USD"

@pytest.mark.django_db
def test_transaction_amount_base():
    user = User.objects.create_user(username="testuser", password="pass")
    cur = Currency.objects.create(code="USD", name="Доллар", rate=3.0)
    cat = Category.objects.create(name="Зарплата", is_income=True, color="#00ff00", user=user)
    tr = Transaction.objects.create(
        user=user, category=cat, amount=100, currency=cur, amount_base=300, date=date.today()
    )
    assert tr.amount_base == 300
