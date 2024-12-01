from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Sum, Q
from django.utils import timezone
from datetime import datetime, timedelta
from django.contrib import messages
from .models import Transaction, Credit, Target, RegularPayment, Category
from django.db.models.functions import TruncMonth
import json

@login_required
def dashboard(request):
    today = timezone.now().date()
    start_of_month = today.replace(day=1)
    week_ago = today - timedelta(days=7)
    
    # Общий баланс и месячные расходы
    total_income = Transaction.objects.filter(
        user=request.user,
        type='income'
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    total_expenses = Transaction.objects.filter(
        user=request.user,
        type='expense'
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    total_balance = total_income - total_expenses
    
    # Расходы за текущий месяц
    monthly_expenses = Transaction.objects.filter(
        user=request.user,
        type='expense',
        date__gte=start_of_month,
        date__lte=today
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Данные для графика баланса (последние 6 месяцев)
    six_months_ago = today - timedelta(days=180)
    monthly_data = Transaction.objects.filter(
        user=request.user,
        date__gte=six_months_ago
    ).annotate(
        month=TruncMonth('date')
    ).values('month', 'type').annotate(
        total=Sum('amount')
    ).order_by('month')

    # Подготовка данных для графиков
    months = []
    income_data = []
    expense_data = []
    balance_data = []
    running_balance = 0
    
    # Получаем начальный баланс до 6 месяцев назад
    initial_balance = Transaction.objects.filter(
        user=request.user,
        date__lt=six_months_ago
    ).aggregate(
        income=Sum('amount', filter=Q(type='income')),
        expenses=Sum('amount', filter=Q(type='expense'))
    )
    running_balance = (initial_balance['income'] or 0) - (initial_balance['expenses'] or 0)

    current_month = six_months_ago.replace(day=1)
    while current_month <= today:
        month_name = current_month.strftime('%B %Y')
        months.append(month_name)
        
        month_income = next(
            (item['total'] for item in monthly_data 
             if item['month'].strftime('%Y-%m') == current_month.strftime('%Y-%m') 
             and item['type'] == 'income'),
            0
        )
        month_expenses = next(
            (item['total'] for item in monthly_data 
             if item['month'].strftime('%Y-%m') == current_month.strftime('%Y-%m') 
             and item['type'] == 'expense'),
            0
        )
        
        running_balance += month_income - month_expenses
        
        income_data.append(float(month_income))
        expense_data.append(float(month_expenses))
        balance_data.append(float(running_balance))
        
        current_month = (current_month + timedelta(days=32)).replace(day=1)

    # Данные расходов за последнюю неделю
    weekly_expenses = []
    for i in range(7):
        date = today - timedelta(days=i)
        daily_expense = Transaction.objects.filter(
            user=request.user,
            type='expense',
            date=date
        ).aggregate(
            total=Sum('amount')
        )['total'] or 0
        weekly_expenses.insert(0, float(daily_expense))

    # Данные для круговой диаграммы расходов по категориям
    category_expenses = Transaction.objects.filter(
        user=request.user,
        type='expense',
        date__gte=start_of_month
    ).values(
        'category__name'
    ).annotate(
        total=Sum('amount')
    ).order_by('-total')

    expense_categories = [item['category__name'] for item in category_expenses]
    expense_distribution = [float(item['total']) for item in category_expenses]
    
    # Получаем цвета категорий
    category_colors = list(Category.objects.filter(
        name__in=expense_categories
    ).values_list('color', flat=True))

    # Расчет процентного изменения расходов
    last_month_start = (start_of_month - timedelta(days=1)).replace(day=1)
    last_month_expenses = Transaction.objects.filter(
        user=request.user,
        type='expense',
        date__gte=last_month_start,
        date__lt=start_of_month
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    if last_month_expenses > 0:
        expense_change = ((monthly_expenses - last_month_expenses) / last_month_expenses) * 100
    else:
        expense_change = 0

    # Активные кредиты и цели
    active_credits = Credit.objects.filter(
        user=request.user,
        end_date__gte=today
    )
    
    active_targets = Target.objects.filter(
        user=request.user,
        deadline__gte=today
    )
    
    # Ближайшие регулярные платежи
    upcoming_payments = RegularPayment.objects.filter(
        user=request.user,
        next_payment_date__gte=today
    ).order_by('next_payment_date')[:5]
    
    # Последние транзакции
    recent_transactions = Transaction.objects.filter(
        user=request.user
    ).select_related('category').order_by('-date')[:5]

    context = {
        'total_balance': total_balance,
        'monthly_expenses': monthly_expenses,
        'expense_change': round(expense_change, 1),
        'active_credits': active_credits,
        'active_targets': active_targets,
        'upcoming_payments': upcoming_payments,
        'recent_transactions': recent_transactions,
        'months': json.dumps(months),
        'income_data': json.dumps(income_data),
        'expense_data': json.dumps(expense_data),
        'balance_data': json.dumps(balance_data),
        'weekly_expenses': json.dumps(weekly_expenses),
        'expense_categories': json.dumps(expense_categories),
        'expense_distribution': json.dumps(expense_distribution),
        'category_colors': json.dumps(category_colors),
        'week_dates': json.dumps([
            (today - timedelta(days=i)).strftime('%d.%m')
            for i in range(6, -1, -1)
        ])
    }
    
    return render(request, 'operations/main.html', context)

@login_required
def transactions(request):
    # Получаем все транзакции пользователя
    transactions_list = Transaction.objects.filter(user=request.user)
    
    # Применяем фильтры
    transaction_type = request.GET.get('type')
    category = request.GET.get('category')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if transaction_type:
        transactions_list = transactions_list.filter(type=transaction_type)
    
    if category:
        transactions_list = transactions_list.filter(category_id=category)
    
    if date_from:
        transactions_list = transactions_list.filter(date__gte=date_from)
    
    if date_to:
        transactions_list = transactions_list.filter(date__lte=date_to)
    
    # Сортировка по дате (новые сверху)
    transactions_list = transactions_list.order_by('-date')
    paginator = Paginator(transactions_list, 10)  # 10 транзакций на страницу
    page = request.GET.get('page')
    transactions = paginator.get_page(page)
    
    # Получаем все категории для текущего пользователя
    categories = Category.objects.filter(user=request.user).order_by('name')
    
    # Статистика для текущего фильтра
    filtered_income = transactions_list.filter(type='income').aggregate(Sum('amount'))['amount__sum'] or 0
    filtered_expenses = transactions_list.filter(type='expense').aggregate(Sum('amount'))['amount__sum'] or 0
    filtered_balance = filtered_income - filtered_expenses
    
    context = {
        'transactions': transactions,
        'categories': categories,
        'filtered_income': filtered_income,
        'filtered_expenses': filtered_expenses,
        'filtered_balance': filtered_balance,
        # Сохраняем параметры фильтрации для формы
        'selected_type': transaction_type,
        'selected_category': category,
        'selected_date_from': date_from,
        'selected_date_to': date_to,
    }
    
    return render(request, 'operations/transactions.html', context)

@login_required
def add_transaction(request):
    if request.method == 'POST':
        # Получаем данные из формы
        transaction_type = request.POST.get('type')
        category_id = request.POST.get('category')
        amount = request.POST.get('amount')
        description = request.POST.get('description')
        date = request.POST.get('date')
        
        # Создаем новую транзакцию
        Transaction.objects.create(
            user=request.user,
            type=transaction_type,
            category_id=category_id,
            amount=amount,
            description=description,
            date=date
        )
        
        return redirect('operations:transactions')
    
    return redirect('operations:transactions')

@login_required
def edit_transaction(request, transaction_id):
    if request.method == 'POST':
        transaction = Transaction.objects.get(id=transaction_id, user=request.user)
        
        transaction.type = request.POST.get('type')
        transaction.category_id = request.POST.get('category')
        transaction.amount = request.POST.get('amount')
        transaction.description = request.POST.get('description')
        transaction.date = request.POST.get('date')
        transaction.save()
        
        return redirect('operations:transactions')
    
    return redirect('operations:transactions')

@login_required
def delete_transaction(request, transaction_id):
    if request.method == 'POST':
        Transaction.objects.filter(id=transaction_id, user=request.user).delete()
    
    return redirect('operations:transactions')

@login_required
def targets(request):
    """Отображение списка финансовых целей"""
    targets = Target.objects.filter(user=request.user).order_by('deadline')
    return render(request, 'targets.html', {'targets': targets})

@login_required
def add_target(request):
    """Добавление новой финансовой цели"""
    if request.method == 'POST':
        try:
            Target.objects.create(
                user=request.user,
                name=request.POST.get('name'),
                target_amount=request.POST.get('target_amount'),
                current_amount=request.POST.get('current_amount', 0),
                deadline=request.POST.get('deadline')
            )
            messages.success(request, 'Цель успешно добавлена')
        except Exception as e:
            messages.error(request, f'Ошибка при добавлении цели: {str(e)}')
    return redirect('operations:targets')

@login_required
def edit_target(request, target_id):
    """Редактирование существующей финансовой цели"""
    if request.method == 'POST':
        target = get_object_or_404(Target, id=target_id, user=request.user)
        try:
            target.name = request.POST.get('name')
            target.target_amount = request.POST.get('target_amount')
            target.current_amount = request.POST.get('current_amount')
            target.deadline = request.POST.get('deadline')
            target.save()
            messages.success(request, 'Цель успешно обновлена')
        except Exception as e:
            messages.error(request, f'Ошибка при обновлении цели: {str(e)}')
    return redirect('operations:targets')

@login_required
def delete_target(request, target_id):
    """Удаление финансовой цели"""
    if request.method == 'POST':
        target = get_object_or_404(Target, id=target_id, user=request.user)
        try:
            target.delete()
            messages.success(request, 'Цель успешно удалена')
        except Exception as e:
            messages.error(request, f'Ошибка при удалении цели: {str(e)}')
    return redirect('operations:targets')

@login_required
def credits(request):
    """Отображение списка кредитов"""
    credits = Credit.objects.filter(user=request.user).order_by('end_date')
    return render(request, 'credits.html', {'credits': credits})

@login_required
def add_credit(request):
    """Добавление нового кредита"""
    if request.method == 'POST':
        try:
            Credit.objects.create(
                user=request.user,
                name=request.POST.get('name'),
                bank=request.POST.get('bank'),
                total_amount=request.POST.get('total_amount'),
                paid_amount=request.POST.get('paid_amount', 0),
                interest_rate=request.POST.get('interest_rate'),
                end_date=request.POST.get('end_date')
            )
            messages.success(request, 'Кредит успешно добавлен')
        except Exception as e:
            messages.error(request, f'Ошибка при добавлении кредита: {str(e)}')
    return redirect('operations:credits')

@login_required
def edit_credit(request, credit_id):
    """Редактирование существующего кредита"""
    if request.method == 'POST':
        credit = get_object_or_404(Credit, id=credit_id, user=request.user)
        try:
            credit.name = request.POST.get('name')
            credit.bank = request.POST.get('bank')
            credit.total_amount = request.POST.get('total_amount')
            credit.paid_amount = request.POST.get('paid_amount')
            credit.interest_rate = request.POST.get('interest_rate')
            credit.end_date = request.POST.get('end_date')
            credit.save()
            messages.success(request, 'Кредит успешно обновлен')
        except Exception as e:
            messages.error(request, f'Ошибка при обновлении кредита: {str(e)}')
    return redirect('operations:credits')

@login_required
def delete_credit(request, credit_id):
    """Удаление кредита"""
    if request.method == 'POST':
        credit = get_object_or_404(Credit, id=credit_id, user=request.user)
        try:
            credit.delete()
            messages.success(request, 'Кредит успешно удален')
        except Exception as e:
            messages.error(request, f'Ошибка при удалении кредита: {str(e)}')
    return redirect('operations:credits')

@login_required
def regular_payments(request):
    """Отображение списка регулярных платежей"""
    regular_payments = RegularPayment.objects.filter(
        user=request.user,
    ).order_by('next_payment_date')
    categories = Category.objects.filter(user=request.user)
    return render(request, 'operations/regular_payments.html', {
        'regular_payments': regular_payments,
        'categories': categories
    })

@login_required
def add_regular_payment(request):
    """Добавление нового регулярного платежа"""
    if request.method == 'POST':
        try:
            category = get_object_or_404(Category, id=request.POST.get('category'), user=request.user)
            RegularPayment.objects.create(
                user=request.user,
                name=request.POST.get('name'),
                amount=request.POST.get('amount'),
                category=category,
                frequency=request.POST.get('frequency'),
                next_payment_date=request.POST.get('next_payment_date'),
                description=request.POST.get('description', '')
            )
            messages.success(request, 'Регулярный платеж успешно добавлен')
        except Exception as e:
            messages.error(request, f'Ошибка при добавлении платежа: {str(e)}')
    return redirect('operations:regular_payments')

@login_required
def edit_regular_payment(request, payment_id):
    """Редактирование существующего регулярного платежа"""
    if request.method == 'POST':
        payment = get_object_or_404(RegularPayment, id=payment_id, user=request.user)
        try:
            category = get_object_or_404(Category, id=request.POST.get('category'), user=request.user)
            payment.name = request.POST.get('name')
            payment.amount = request.POST.get('amount')
            payment.category = category
            payment.frequency = request.POST.get('frequency')
            payment.next_payment_date = request.POST.get('next_payment_date')
            payment.description = request.POST.get('description', '')
            payment.save()
            messages.success(request, 'Регулярный платеж успешно обновлен')
        except Exception as e:
            messages.error(request, f'Ошибка при обновлении платежа: {str(e)}')
    return redirect('operations:regular_payments')

@login_required
def delete_regular_payment(request, payment_id):
    """Удаление регулярного платежа"""
    if request.method == 'POST':
        payment = get_object_or_404(RegularPayment, id=payment_id, user=request.user)
        try:
            payment.delete()
            messages.success(request, 'Регулярный платеж успешно удален')
        except Exception as e:
            messages.error(request, f'Ошибка при удалении платежа: {str(e)}')
    return redirect('operations:regular_payments')

@login_required
def analytics(request):
    # Здесь будет логика для аналитики
    return render(request, 'operations/analytics.html')

@login_required
def main(request):
    """Главная страница с общей статистикой"""
    today = timezone.now()
    start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Статистика за текущий месяц
    monthly_stats = Transaction.objects.filter(
        user=request.user,
        date__gte=start_of_month,
        date__lte=today
    ).aggregate(
        income=Sum('amount', filter=Q(type='income')),
        expenses=Sum('amount', filter=Q(type='expense'))
    )
    
    monthly_income = monthly_stats['income'] or 0
    monthly_expenses = monthly_stats['expenses'] or 0
    balance = monthly_income - monthly_expenses

    # Активные цели
    active_targets = Target.objects.filter(
        user=request.user,
        next_payment_date__gte=today
    ).count()

    # Данные для графика за последние 6 месяцев
    six_months_ago = today - timedelta(days=180)
    monthly_data = Transaction.objects.filter(
        user=request.user,
        date__gte=six_months_ago
    ).annotate(
        month=TruncMonth('date')
    ).values('month', 'type').annotate(
        total=Sum('amount')
    ).order_by('month')

    # Подготовка данных для графиков
    months = []
    income_data = []
    expense_data = []
    current_month = six_months_ago.replace(day=1)
    
    while current_month <= today:
        month_name = current_month.strftime('%B %Y')
        months.append(month_name)
        
        month_income = next(
            (item['total'] for item in monthly_data 
             if item['month'].strftime('%Y-%m') == current_month.strftime('%Y-%m') 
             and item['type'] == 'income'),
            0
        )
        month_expenses = next(
            (item['total'] for item in monthly_data 
             if item['month'].strftime('%Y-%m') == current_month.strftime('%Y-%m') 
             and item['type'] == 'expense'),
            0
        )
        
        income_data.append(float(month_income))
        expense_data.append(float(month_expenses))
        current_month = (current_month + timedelta(days=32)).replace(day=1)

    # Данные для круговой диаграммы расходов
    expense_by_category = Transaction.objects.filter(
        user=request.user,
        type='expense',
        date__gte=start_of_month
    ).values(
        'category__name'
    ).annotate(
        total=Sum('amount')
    ).order_by('-total')[:8]

    expense_categories = [item['category__name'] for item in expense_by_category]
    expense_distribution = [float(item['total']) for item in expense_by_category]

    # Последние транзакции
    recent_transactions = Transaction.objects.filter(
        user=request.user
    ).select_related('category').order_by('-date')[:5]

    context = {
        'monthly_income': monthly_income,
        'monthly_expenses': monthly_expenses,
        'balance': balance,
        'active_targets': active_targets,
        'months': json.dumps(months),
        'income_data': income_data,
        'expense_data': expense_data,
        'expense_categories': json.dumps(expense_categories),
        'expense_distribution': expense_distribution,
        'recent_transactions': recent_transactions,
    }
    
    return render(request, 'operations/main.html', context)