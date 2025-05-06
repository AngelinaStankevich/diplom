from django.urls import path, include
from . import views
from .views import TransactionCreateView

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('add_transaction/', views.add_transaction, name='add_transaction'),
    path('add_category/', views.add_category, name='add_category'),
    path('add_budget/', views.add_budget, name='add_budget'),
    path('register/', views.register, name='register'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('analytics/', views.analytics, name='analytics'),
    path('export_csv/', views.export_transactions_csv, name='export_csv'),
    path('import_csv/', views.import_transactions_csv, name='import_csv'),
    path('transactions/', views.transactions_list, name='transactions_list'),
    path('recurring/', views.recurring_transactions, name='recurring_transactions'),
    path('process-recurring/', views.process_recurring_transactions, name='process_recurring'),
    path('recurring/delete/<int:pk>/', views.delete_recurring_transaction, name='delete_recurring'),
    path('monthly-summary/', views.monthly_summary, name='monthly_summary'),
    path('add_monthly_budget/', views.add_monthly_budget, name='add_monthly_budget'),
    path('budget_settings/', views.budget_settings, name='budget_settings'),
    path('edit_monthly_budget/<int:pk>/', views.edit_monthly_budget, name='edit_monthly_budget'),
    path('transactions/create/', TransactionCreateView.as_view(), name='transaction_create'),
]