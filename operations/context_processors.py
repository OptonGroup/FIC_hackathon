from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
from .models import Transaction, Credit, Target, RegularPayment
import json

def financial_data(request):
    if not request.user.is_authenticated:
        return {}

    today = timezone.now().date()
    start_of_current_month = today.replace(day=1)
    # Получаем начало предыдущего месяца
    start_of_previous_month = (start_of_current_month - timedelta(days=1)).replace(day=1)

    # Получаем данные о доходах и расходах за последние 30 дней
    monthly_transactions = Transaction.objects.filter(
        user=request.user,
        date__gte=start_of_previous_month,
        date__lt=start_of_current_month
    )

    # Считаем доходы и расходы за предыдущий месяц
    income = monthly_transactions.filter(type='income').aggregate(
        total=Sum('amount')
    )['total'] or 0

    expenses = monthly_transactions.filter(type='expense').aggregate(
        total=Sum('amount')
    )['total'] or 0

    # Получаем категории расходов за предыдущий месяц
    expense_categories = monthly_transactions.filter(
        type='expense'
    ).values('category__name').annotate(
        total=Sum('amount')
    ).order_by('-total')[:5]

    # Формируем списки для передачи в шаблон
    categories_data = []
    for cat in expense_categories:
        if cat['category__name']:
            categories_data.append({
                'name': cat['category__name'],
                'amount': float(cat['total'])
            })

    return {
        'total_income': income,
        'total_expenses': expenses,
        'total_balance': income - expenses,
        'expense_categories_data': categories_data,
        'active_credits': Credit.objects.filter(
            user=request.user,
            end_date__gte=today
        ),
        'active_targets': Target.objects.filter(
            user=request.user,
            deadline__gte=today
        ),
        'upcoming_payments': RegularPayment.objects.filter(
            user=request.user,
            next_payment_date__gte=today
        ).order_by('next_payment_date')[:5],
        'report_period': f"с {start_of_previous_month.strftime('%d.%m.%Y')} по {(start_of_current_month - timedelta(days=1)).strftime('%d.%m.%Y')}"
    } 