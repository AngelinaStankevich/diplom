from django.db import models
from django.contrib.auth.models import User

class Category(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_income = models.BooleanField(default=False)  # Доход или расход
    color = models.CharField(max_length=7, default="#6c757d")  # HEX-цвет

    def __str__(self):
        return self.name

class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    description = models.TextField(blank=True, null=True)
    currency = models.ForeignKey('Currency', on_delete=models.PROTECT)
    amount_base = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.category}: {self.amount}"

    def save(self, *args, **kwargs):
        if self.currency:
            self.amount_base = self.amount * self.currency.rate
        super().save(*args, **kwargs)

class Budget(models.Model): 
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    limit = models.DecimalField(max_digits=10, decimal_places=2)
    month = models.DateField()  
    currency = models.ForeignKey('Currency', on_delete=models.PROTECT, default=1)  # default=1 — BYN

    def __str__(self):
        return f"{self.category} - {self.limit} {self.currency.symbol} ({self.month})"

class RecurringTransaction(models.Model):
    FREQUENCY_CHOICES = [
        ('monthly', 'Ежемесячно'),
        ('weekly', 'Еженедельно'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.ForeignKey('Currency', on_delete=models.PROTECT)  # Добавляем поле валюты
    description = models.TextField(blank=True, null=True)
    frequency = models.CharField(max_length=10, choices=FREQUENCY_CHOICES)
    start_date = models.DateField()
    next_date = models.DateField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.category}: {self.amount} {self.currency.symbol} ({self.get_frequency_display()})"

class Currency(models.Model):
    code = models.CharField(max_length=3)  # Например, USD, EUR, RUB
    name = models.CharField(max_length=50)  # Доллар США, Евро, Рубль
    symbol = models.CharField(max_length=5)  # $, €, ₽
    rate = models.DecimalField(max_digits=10, decimal_places=4)  # Курс к основной валюте

    class Meta:
        verbose_name_plural = "currencies"

    def __str__(self):
        return f"{self.code} ({self.symbol})"

class MonthlyBudget(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    month = models.DateField()
    income_plan = models.DecimalField(max_digits=10, decimal_places=2)
    expense_plan = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.ForeignKey('Currency', on_delete=models.PROTECT, default=1)  # default=1 — BYN
    notes = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ['user', 'month']

    def __str__(self):
        return f"Бюджет на {self.month.strftime('%B %Y')}"

class UserPreferences(models.Model):
    BUDGET_TYPE_CHOICES = [
        ('monthly', 'Общий месячный бюджет'),
        ('category', 'Бюджет по категориям'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    budget_type = models.CharField(
        max_length=10,
        choices=BUDGET_TYPE_CHOICES,
        default='monthly'
    )

    def __str__(self):
        return f"Настройки пользователя {self.user.username}"