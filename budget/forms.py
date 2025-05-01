from django import forms
from .models import Category, Transaction, Budget, RecurringTransaction, MonthlyBudget, UserPreferences
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class CategoryForm(forms.ModelForm):
    color = forms.CharField(
        widget=forms.TextInput(attrs={'type': 'color'}),
        label='Цвет категории'
    )

    class Meta:
        model = Category
        fields = ['name', 'is_income', 'color']

class TransactionForm(forms.ModelForm):
    date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'})
    )

    class Meta:
        model = Transaction
        fields = ['category', 'amount', 'currency', 'date', 'description']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'})
        }

class BudgetForm(forms.ModelForm):
    month = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'month'}),
        label='Месяц',
        input_formats=['%Y-%m']
    )

    class Meta:
        model = Budget
        fields = ['category', 'limit', 'currency', 'month']

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

class ImportCSVForm(forms.Form):
    file = forms.FileField(label="Выберите CSV-файл")

class TransactionFilterForm(forms.Form):
    OPERATION_TYPE_CHOICES = [
        ('all', 'Все'),
        ('income', 'Доходы'),
        ('expense', 'Расходы'),
    ]
    operation_type = forms.ChoiceField(
        choices=OPERATION_TYPE_CHOICES,
        required=False,
        label='Тип операции',
        initial='all'
    )
    search = forms.CharField(
        required=False,
        label='Поиск по описанию',
        widget=forms.TextInput(attrs={'placeholder': 'Поиск...'})
    )
    category = forms.ModelChoiceField(
        required=False,
        queryset=None,
        label='Категория'
    )
    date_from = forms.DateField(
        required=False,
        label='С даты',
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    date_to = forms.DateField(
        required=False,
        label='По дату',
        widget=forms.DateInput(attrs={'type': 'date'})
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.filter(user=user)

class RecurringTransactionForm(forms.ModelForm):
    class Meta:
        model = RecurringTransaction
        fields = ['category', 'amount', 'currency', 'description', 'frequency', 'start_date']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'})
        }

class MonthlyBudgetForm(forms.ModelForm):
    month = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'month'}),
        label='Месяц',
        input_formats=['%Y-%m']
    )
    income_plan = forms.DecimalField(
        label='Планируемый доход',
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00'})
    )
    expense_plan = forms.DecimalField(
        label='Планируемые расходы',
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00'})
    )
    notes = forms.CharField(
        label='Заметки',
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'})
    )

    class Meta:
        model = MonthlyBudget
        fields = ['month', 'income_plan', 'expense_plan', 'currency', 'notes']

class UserPreferencesForm(forms.ModelForm):
    class Meta:
        model = UserPreferences
        fields = ['budget_type']
        labels = {
            'budget_type': 'Тип бюджетирования'
        }