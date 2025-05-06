from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Category, Transaction, Budget, RecurringTransaction, MonthlyBudget, UserPreferences
from .forms import CategoryForm, TransactionForm, BudgetForm, RegisterForm, ImportCSVForm, TransactionFilterForm, RecurringTransactionForm, MonthlyBudgetForm, UserPreferencesForm
from django.contrib.auth import login
from django.db.models import Sum
from datetime import date, datetime, timedelta
from django.utils import timezone
import csv
from django.http import HttpResponse
from io import TextIOWrapper
from django.contrib import messages
from django.db.models.functions import TruncMonth
from django.views.generic.edit import CreateView

@login_required
def dashboard(request):
    today = date.today()
    
    # Получаем предпочтения пользователя
    preferences, created = UserPreferences.objects.get_or_create(user=request.user)
    
    # Общие данные для обоих типов бюджета
    expense_categories = Category.objects.filter(user=request.user, is_income=False)
    income_categories = Category.objects.filter(user=request.user, is_income=True)
    
    context = {
        'expense_categories': expense_categories,
        'income_categories': income_categories,
        'budget_type': preferences.budget_type,
    }
    
    if preferences.budget_type == 'monthly':
        # Логика для месячного бюджета
        monthly_budget = MonthlyBudget.objects.filter(
            user=request.user,
            month__year=today.year,
            month__month=today.month
        ).first()
        
        if monthly_budget:
            context['monthly_summary'] = get_monthly_summary(request.user, monthly_budget)
    else:
        # Логика для бюджета по категориям
        budgets = Budget.objects.filter(
            user=request.user,
            month__year=today.year,
            month__month=today.month
        ).select_related('category', 'currency')
        
        context['budget_data'] = get_category_budget_data(request.user, budgets)
    
    return render(request, 'budget/dashboard.html', context)

@login_required
def add_transaction(request):
    category_id = request.GET.get('category')
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.save()
            return redirect('dashboard')
    else:
        if category_id:
            form = TransactionForm(initial={'category': category_id})
        else:
            form = TransactionForm()
    return render(request, 'budget/add_transaction.html', {'form': form})

@login_required
def add_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.user = request.user
            category.save()
            return redirect('dashboard')
    else:
        form = CategoryForm()
    return render(request, 'budget/add_category.html', {'form': form})

@login_required
def add_budget(request):
    if request.method == 'POST':
        form = BudgetForm(request.POST)
        if form.is_valid():
            budget = form.save(commit=False)
            budget.user = request.user
            budget.save()
            return redirect('dashboard')
    else:
        form = BudgetForm()
    return render(request, 'budget/add_budget.html', {'form': form})

@login_required
def add_monthly_budget(request):
    if request.method == 'POST':
        form = MonthlyBudgetForm(request.POST)
        if form.is_valid():
            budget = form.save(commit=False)
            budget.user = request.user
            
            # Проверяем, нет ли уже бюджета на этот месяц
            existing_budget = MonthlyBudget.objects.filter(
                user=request.user,
                month__year=budget.month.year,
                month__month=budget.month.month
            ).first()
            
            if existing_budget:
                messages.error(request, 'Бюджет на этот месяц уже существует')
                return render(request, 'budget/add_monthly_budget.html', {'form': form})
            
            budget.save()
            messages.success(request, 'Месячный бюджет успешно создан')
            return redirect('dashboard')
    else:
        # Устанавливаем текущий месяц по умолчанию
        initial_date = date.today().replace(day=1)
        form = MonthlyBudgetForm(initial={'month': initial_date})
    
    return render(request, 'budget/add_monthly_budget.html', {'form': form})

def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = RegisterForm()
    return render(request, "registration/register.html", {"form": form})

@login_required
def analytics(request):
    # По умолчанию — текущий месяц
    today = timezone.now().date()
    month = request.GET.get('month', today.strftime('%Y-%m'))
    year, month_num = map(int, month.split('-'))
    start_date = date(year, month_num, 1)
    if month_num == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month_num + 1, 1)

    # Получаем все месяцы, за которые есть транзакции
    available_months = (Transaction.objects
        .filter(user=request.user)
        .dates('date', 'month', order='DESC')
        .distinct())

    # Суммируем расходы по категориям
    categories = Category.objects.filter(user=request.user, is_income=False)
    data = (
        Transaction.objects
        .filter(user=request.user, date__gte=start_date, date__lt=end_date, category__in=categories)
        .values('category__name', 'category__color')
        .annotate(total=Sum('amount_base'))
        .order_by('-total')
    )

    labels = [item['category__name'] for item in data]
    values = [float(item['total']) for item in data]
    colors = [item['category__color'] or '#6c757d' for item in data]
    
    # Подсчитываем статистику
    total_expenses = sum(values) if values else 0
    avg_expense = total_expenses / len(values) if values else 0
    max_expense = max(values) if values else 0
    categories_count = len(values)

    # Получаем данные по месяцам для графика трендов
    monthly_trends = (
        Transaction.objects
        .filter(user=request.user, category__in=categories)
        .annotate(month=TruncMonth('date'))
        .values('month')
        .annotate(total=Sum('amount_base'))
        .order_by('month')
    )

    trend_labels = [item['month'].strftime('%B %Y') for item in monthly_trends]
    trend_values = [float(item['total']) for item in monthly_trends]

    return render(request, 'budget/analytics.html', {
        'labels': labels,
        'values': values,
        'colors': colors,
        'month': month,
        'available_months': available_months,
        'total_expenses': total_expenses,
        'avg_expense': avg_expense,
        'max_expense': max_expense,
        'categories_count': categories_count,
        'trend_labels': trend_labels,
        'trend_values': trend_values,
    })

@login_required
def export_transactions_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="transactions.csv"'

    # Добавляем BOM для корректного открытия в Excel
    response.write('\ufeff'.encode('utf8'))

    writer = csv.writer(response)
    writer.writerow(['Дата', 'Категория', 'Сумма', 'Описание'])

    transactions = Transaction.objects.filter(user=request.user).order_by('-date')
    for t in transactions:
        writer.writerow([t.date, t.category.name, t.amount, t.description])

    return response

@login_required
def import_transactions_csv(request):
    if request.method == 'POST':
        form = ImportCSVForm(request.POST, request.FILES)
        if form.is_valid():
            file = form.cleaned_data['file']
            # Открываем файл с правильной кодировкой
            csv_file = TextIOWrapper(file, encoding='utf-8')
            reader = csv.reader(csv_file)
            next(reader)  # Пропускаем заголовок
            count = 0
            for row in reader:
                try:
                    date, category_name, amount, description = row
                    category, _ = Category.objects.get_or_create(
                        user=request.user, name=category_name, is_income=False
                    )
                    Transaction.objects.create(
                        user=request.user,
                        category=category,
                        amount=amount,
                        date=date,
                        description=description
                    )
                    count += 1
                except Exception as e:
                    continue
            messages.success(request, f'Импортировано операций: {count}')
            return redirect('dashboard')
    else:
        form = ImportCSVForm()
    return render(request, 'budget/import_csv.html', {'form': form})

@login_required
def transactions_list(request):
    transactions = Transaction.objects.filter(user=request.user)
    form = TransactionFilterForm(request.user, request.GET)

    # Получаем все доступные месяцы для фильтрации
    available_months = (Transaction.objects
        .filter(user=request.user)
        .dates('date', 'month', order='DESC')
        .distinct())

    if form.is_valid():
        op_type = form.cleaned_data.get('operation_type')
        if op_type == 'income':
            transactions = transactions.filter(category__is_income=True)
        elif op_type == 'expense':
            transactions = transactions.filter(category__is_income=False)
        if form.cleaned_data['search']:
            transactions = transactions.filter(
                description__icontains=form.cleaned_data['search']
            )
        if form.cleaned_data['category']:
            transactions = transactions.filter(
                category=form.cleaned_data['category']
            )
        if form.cleaned_data['date_from']:
            transactions = transactions.filter(
                date__gte=form.cleaned_data['date_from']
            )
        if form.cleaned_data['date_to']:
            transactions = transactions.filter(
                date__lte=form.cleaned_data['date_to']
            )

    transactions = transactions.select_related('category', 'currency').order_by('-date')

    return render(request, 'budget/transactions_list.html', {
        'transactions': transactions,
        'form': form,
        'available_months': available_months,
    })

@login_required
def recurring_transactions(request):
    if request.method == 'POST':
        form = RecurringTransactionForm(request.POST)
        if form.is_valid():
            recurring = form.save(commit=False)
            recurring.user = request.user
            recurring.next_date = form.cleaned_data['start_date']
            recurring.save()
            messages.success(request, 'Регулярная операция создана!')
            return redirect('recurring_transactions')
    else:
        form = RecurringTransactionForm()

    recurring_list = RecurringTransaction.objects.filter(user=request.user)
    return render(request, 'budget/recurring_transactions.html', {
        'form': form,
        'recurring_list': recurring_list
    })

@login_required
def process_recurring_transactions(request):
    today = timezone.now().date()
    recurring = RecurringTransaction.objects.filter(
        user=request.user,
        is_active=True,
        next_date__lte=today
    )

    created_count = 0
    for item in recurring:
        # Создаем транзакцию с учетом валюты
        Transaction.objects.create(
            user=request.user,
            category=item.category,
            amount=item.amount,
            currency=item.currency,  # Добавляем валюту
            date=item.next_date,
            description=f"Регулярный платеж: {item.description}"
        )
        created_count += 1

        # Обновляем дату следующей операции
        if item.frequency == 'monthly':
            item.next_date = item.next_date + timedelta(days=30)
        elif item.frequency == 'weekly':
            item.next_date = item.next_date + timedelta(days=7)
        item.save()

    messages.success(request, f'Создано {created_count} регулярных операций')
    return redirect('recurring_transactions')

@login_required
def delete_recurring_transaction(request, pk):
    recurring = get_object_or_404(RecurringTransaction, pk=pk, user=request.user)
    if request.method == 'POST':
        recurring.delete()
        messages.success(request, 'Регулярная операция удалена')
        return redirect('recurring_transactions')
    return render(request, 'budget/delete_recurring.html', {'recurring': recurring})

@login_required
def monthly_summary(request):
    # Получаем все транзакции пользователя, сгруппированные по месяцам
    monthly_transactions = (
        Transaction.objects
        .filter(user=request.user)
        .annotate(month=TruncMonth('date'))
        .values('month', 'currency__code', 'currency__symbol', 'category__is_income')
        .annotate(
            total=Sum('amount'),
            total_byn=Sum('amount_base')  # Сумма в BYN
        )
        .order_by('-month', 'currency__code')
    )

    # Получаем все месяцы, за которые есть бюджеты
    budgets = MonthlyBudget.objects.filter(user=request.user).order_by('-month')

    # Группируем по месяцам
    summary = {}
    yearly_summary = {}

    for transaction in monthly_transactions:
        month_key = transaction['month'].strftime('%Y-%m')
        year_key = transaction['month'].strftime('%Y')
        
        if month_key not in summary:
            summary[month_key] = {
                'expenses': [],
                'incomes': [],
                'total_expenses_byn': 0,
                'total_incomes_byn': 0,
                'budget': None
            }
        
        if year_key not in yearly_summary:
            yearly_summary[year_key] = {
                'total_expenses_byn': 0,
                'total_incomes_byn': 0
            }

        # Добавляем данные о бюджете
        for budget in budgets:
            if budget.month.strftime('%Y-%m') == month_key:
                summary[month_key]['budget'] = {
                    'income_plan': budget.income_plan,
                    'expense_plan': budget.expense_plan,
                    'currency': budget.currency,
                    'notes': budget.notes
                }
                break

        # Добавляем транзакцию
        transaction_data = {
            'currency_code': transaction['currency__code'],
            'currency_symbol': transaction['currency__symbol'],
            'total': transaction['total'],
            'total_byn': transaction['total_byn']
        }

        if transaction['category__is_income']:
            summary[month_key]['incomes'].append(transaction_data)
            summary[month_key]['total_incomes_byn'] += transaction['total_byn']
            yearly_summary[year_key]['total_incomes_byn'] += transaction['total_byn']
        else:
            summary[month_key]['expenses'].append(transaction_data)
            summary[month_key]['total_expenses_byn'] += transaction['total_byn']
            yearly_summary[year_key]['total_expenses_byn'] += transaction['total_byn']

    # Сортируем по месяцам (от новых к старым)
    summary = dict(sorted(summary.items(), reverse=True))
    yearly_summary = dict(sorted(yearly_summary.items(), reverse=True))

    return render(request, 'budget/monthly_summary.html', {
        'summary': summary,
        'yearly_summary': yearly_summary,
    })

@login_required
def budget_settings(request):
    preferences, created = UserPreferences.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = UserPreferencesForm(request.POST, instance=preferences)
        if form.is_valid():
            form.save()
            messages.success(request, 'Настройки бюджета обновлены')
            return redirect('dashboard')
    else:
        form = UserPreferencesForm(instance=preferences)
    
    return render(request, 'budget/budget_settings.html', {'form': form})

def get_monthly_summary(user, monthly_budget):
    """Получение сводки по месячному бюджету"""
    today = date.today()
    
    # Получаем все транзакции за текущий месяц
    month_transactions = Transaction.objects.filter(
        user=user,
        date__year=today.year,
        date__month=today.month
    )

    # Считаем фактические доходы и расходы
    actual_income = month_transactions.filter(
        category__is_income=True
    ).aggregate(total=Sum('amount_base'))['total'] or 0

    actual_expenses = month_transactions.filter(
        category__is_income=False
    ).aggregate(total=Sum('amount_base'))['total'] or 0

    # Конвертируем планы в базовую валюту (BYN)
    income_plan_byn = monthly_budget.income_plan * monthly_budget.currency.rate
    expense_plan_byn = monthly_budget.expense_plan * monthly_budget.currency.rate
    
    return {
        'id': monthly_budget.id,
        'income_plan': monthly_budget.income_plan,
        'expense_plan': monthly_budget.expense_plan,
        'currency': monthly_budget.currency,
        'income_plan_byn': income_plan_byn,
        'expense_plan_byn': expense_plan_byn,
        'actual_income': actual_income,
        'actual_expenses': actual_expenses,
        'income_progress': (actual_income / income_plan_byn * 100) if income_plan_byn else 0,
        'expense_progress': (actual_expenses / expense_plan_byn * 100) if expense_plan_byn else 0,
        'balance_plan': income_plan_byn - expense_plan_byn,
        'balance_actual': actual_income - actual_expenses,
        'notes': monthly_budget.notes
    }

def get_category_budget_data(user, budgets):
    """Получение данных о бюджетах по категориям"""
    today = date.today()
    budget_data = []
    
    for budget in budgets:
        # Считаем потраченное в BYN (amount_base)
        spent = Transaction.objects.filter(
            user=user,
            category=budget.category,
            date__year=budget.month.year,
            date__month=budget.month.month
        ).aggregate(total=Sum('amount_base'))['total'] or 0

        # Лимит бюджета в BYN
        budget_limit_byn = budget.limit * budget.currency.rate

        left = budget_limit_byn - spent
        exceeded = spent > budget_limit_byn

        budget_data.append({
            'category': budget.category,
            'limit': budget.limit,
            'currency': budget.currency,
            'limit_byn': budget_limit_byn,
            'spent': spent,
            'left': left,
            'exceeded': exceeded,
        })
    
    return budget_data

@login_required
def edit_monthly_budget(request, pk):
    budget = get_object_or_404(MonthlyBudget, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = MonthlyBudgetForm(request.POST, instance=budget)
        if form.is_valid():
            form.save()
            messages.success(request, 'Месячный бюджет успешно обновлен')
            return redirect('dashboard')
    else:
        form = MonthlyBudgetForm(instance=budget)
    
    return render(request, 'budget/edit_monthly_budget.html', {
        'form': form,
        'budget': budget
    })

class TransactionCreateView(CreateView):
    model = Transaction
    fields = ['category', 'amount', 'currency', 'date', 'description']
    template_name = 'budget/transaction_form.html'
    success_url = '/'  # или другой URL, куда перенаправлять после создания