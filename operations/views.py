from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Sum, Q
from django.utils import timezone
from datetime import datetime, timedelta
from django.contrib import messages
from .models import Transaction, Credit, Target, RegularPayment, Category, Card
from django.db.models.functions import TruncMonth
import json
from decimal import Decimal
import requests

def get_currency_rates():
    # Заглушка с фиксированными значениями
    return {
        'USD': Decimal('96.74'),
        'EUR': Decimal('104.52'),
        'CNY': Decimal('13.41'),
        'BTC': format_number(Decimal('4325789.45'))  # Форматируем число прямо здесь
    }

def format_number(number):
    """Форматирует большие числа с разделителями"""
    return '{:,.0f}'.format(number).replace(',', ' ')

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
    
    # Создаем список различных цветов для категорий
    category_colors = [
        '#FF6384',  # красный
        '#36A2EB',  # синий
        '#FFCE56',  # желтый
        '#4BC0C0',  # бирюзовый
        '#9966FF',  # фиолетовый
        '#FF9F40',  # оранжевый
        '#7FFF00',  # зеленый
        '#FF69B4',  # розовый
        '#20B2AA',  # морской
        '#BA55D3',  # пурпурный
    ]
    
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

    currency_rates = get_currency_rates()

    # Словарь с цветами для разных дизайнов карт
    CARD_DESIGN_COLORS = {
        'classic_black': '#212529',  # Черный
        'classic_white': '#f8f9fa',  # Белый
        'gold': '#ffd700',          # Золотой
        'platinum': '#e5e4e2',      # Платиновый
        'metal': '#71797E',         # Металлик
    }
    
    # Добавляем цвета для карт
    for transaction in recent_transactions:
        if transaction.card:
            transaction.card.design_color = CARD_DESIGN_COLORS.get(transaction.card.design, '#6c757d')

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
        ]),
        'currency_rates': currency_rates,
    }
    
    return render(request, 'operations/main.html', context)

@login_required
def transactions(request):
    """Отображение списка транзакций"""
    # Получаем все транзакции пользователя
    transactions_list = Transaction.objects.filter(user=request.user)
    
    # Применяем фильтры
    transaction_type = request.GET.get('type')
    category = request.GET.get('category')
    card = request.GET.get('card')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if transaction_type:
        transactions_list = transactions_list.filter(type=transaction_type)
    
    if category:
        transactions_list = transactions_list.filter(category_id=category)
        
    if card:
        transactions_list = transactions_list.filter(card_id=card)
    
    if date_from:
        transactions_list = transactions_list.filter(date__gte=date_from)
    
    if date_to:
        transactions_list = transactions_list.filter(date__lte=date_to)
    
    # Сортировка
    sort_field = request.GET.get('sort', '-date')
    if request.GET.get('desc'):
        sort_field = f"-{sort_field.replace('-', '')}"
    else:
        sort_field = sort_field.replace('-', '')
    
    sort_mapping = {
        'date': 'date',
        'type': 'type',
        'category': 'category__name',
        'amount': 'amount',
        'card': 'card__name'
    }
    
    if sort_field.replace('-', '') in sort_mapping:
        sort_field = f"{'-' if sort_field.startswith('-') else ''}{sort_mapping[sort_field.replace('-', '')]}"
        transactions_list = transactions_list.order_by(sort_field)
    
    # Пагинация
    paginator = Paginator(transactions_list, 10)
    page = request.GET.get('page')
    transactions = paginator.get_page(page)
    
    transactions = transactions_list.select_related('card', 'category').all()
    
    context = {
        'transactions': transactions,
        'categories': Category.objects.filter(user=request.user),
        'cards': Card.objects.select_related().filter(user=request.user),
        'selected_type': transaction_type,
        'selected_category': int(category) if category else None,
        'selected_card': int(card) if card else None,
        'selected_date_from': date_from,
        'selected_date_to': date_to,
    }
    
    return render(request, 'operations/transactions.html', context)

@login_required
def add_transaction(request):
    """Добавление новой транзакции"""
    if request.method == 'POST':
        try:
            # Получаем карту и проверяем, что она принадлежит пользователю
            card_id = request.POST.get('card')
            if not card_id:
                raise ValueError('Не выбрана карта')
                
            card = get_object_or_404(Card, id=card_id, user=request.user)
            category = get_object_or_404(Category, id=request.POST.get('category'), user=request.user)
            amount = Decimal(request.POST.get('amount'))
            
            # Создаем транзакцию с указанием карты
            transaction = Transaction.objects.create(
                user=request.user,
                card=card,  # Добавляем карту
                type=request.POST.get('type'),
                amount=amount,
                category=category,
                description=request.POST.get('description', ''),
                date=request.POST.get('date')
            )
            
            # Обновляем баланс карты
            if transaction.type == 'income':
                card.balance += amount
            else:
                card.balance -= amount
            card.save()
            
            messages.success(request, 'Транзакция успешно добавлена')
        except Card.DoesNotExist:
            messages.error(request, 'Выбранная карта не найдена')
        except Category.DoesNotExist:
            messages.error(request, 'Выбранная категория не найдена')
        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f'Ошибка при добавлении транзакции: {str(e)}')
    
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
    
    # Получаем курсы валют (уже отформатированные)
    currency_rates = get_currency_rates()
    
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
        'currency_rates': currency_rates,
    }
    
    return render(request, 'operations/main.html', context)

@login_required
def cards(request):
    """Отображение списка карт пользователя"""
    cards = Card.objects.filter(user=request.user)
    context = {
        'cards': cards,
        'card_types': Card.CARD_TYPES,
        'card_designs': Card.CARD_DESIGNS,
    }
    return render(request, 'operations/cards.html', context)


def get_bank_by_card_number(card_number):
    bin_number = card_number[:6]
    url = f"https://lookup.binlist.net/{bin_number}"
    response = requests.get(url)
    response.raise_for_status()
    bank_info = response.json()
    bank_name = bank_info.get('bank', {}).get('name', 'Неизвестно')
    bank_country = bank_info.get('country', {}).get('name', 'Неизвестно')
    card_type = bank_info.get('type', 'Неизвестно')
    print(card_type)

    return {
        'bank_name': bank_name,
        'bank_country': bank_country,
        'card_type': card_type
    }

@login_required
def add_card(request):
    """Добавление новой карты"""
    if request.method == 'POST':
        try:
            # Очистка номера карты от пробелов
            card_number = request.POST.get('card_number').replace(' ', '')
            
            card_info = get_bank_by_card_number(card_number)
            
            Card.objects.create(
                user=request.user,
                name=request.POST.get('name'),
                card_number=card_number,
                bank=card_info['bank_name'],
                card_type=card_info['card_type'],
                design=request.POST.get('design'),
                balance=request.POST.get('balance', 0)
            )

            # Card.objects.create(
            #     user=request.user,
            #     name=request.POST.get('name'),
            #     card_number=card_number,
            #     bank=request.POST.get('bank'),
            #     card_type=request.POST.get('card_type'),
            #     design=request.POST.get('design'),
            #     balance=request.POST.get('balance', 0)
            # )
            messages.success(request, 'Карта успешно добавлена')
        except Exception as e:
            messages.error(request, f'Ошибка при добавлении карты: {str(e)}')
    return redirect('operations:cards')

@login_required
def edit_card(request, card_id):
    """Редактирование существующей карты"""
    if request.method == 'POST':
        card = get_object_or_404(Card, id=card_id, user=request.user)
        try:
            card_number = request.POST.get('card_number').replace(' ', '')
            card_info = get_bank_by_card_number(card_number)
            card.name = request.POST.get('name')
            card.card_number = card_number
            # card.bank = request.POST.get('bank')
            # card.card_type = request.POST.get('card_type')
            card.bank = card_info['bank_name']
            card.card_type = card_info['card_type']
            card.design = request.POST.get('design')
            card.balance = request.POST.get('balance')
            card.save()
            
            messages.success(request, 'Карта успешно обновлена')
        except Exception as e:
            messages.error(request, f'Ошибка при обновлении карты: {str(e)}')
    return redirect('operations:cards')

@login_required
def delete_card(request, card_id):
    """Удаление карты"""
    if request.method == 'POST':
        card = get_object_or_404(Card, id=card_id, user=request.user)
        try:
            # Проверяем, есть ли транзакции, связанные с картой
            if Transaction.objects.filter(card=card).exists():
                messages.error(request, 'Невозможно удалить карту, с которой совершались транзакции')
            else:
                card.delete()
                messages.success(request, 'Карта успешно удалена')
        except Exception as e:
            messages.error(request, f'Ошибка при удалении карты: {str(e)}')
    return redirect('operations:cards')

@login_required
def calendar(request):
    """Отображение календаря с транзакциями"""
    today = timezone.now().date()
    year = int(request.GET.get('year', today.year))
    month = int(request.GET.get('month', today.month))
    
    # Получаем первый и последний день месяца
    first_day = datetime(year, month, 1).date()
    if month == 12:
        last_day = datetime(year + 1, 1, 1).date() - timedelta(days=1)
    else:
        last_day = datetime(year, month + 1, 1).date() - timedelta(days=1)
    
    # Определяем, сколько пустых ячеек нужно в начале (0 = понедельник, 6 = воскресенье)
    first_weekday = first_day.weekday()
    
    # Создаем список для всех дней месяца, включая пустые ячейки
    calendar_data = []
    
    # Добавляем пустые ячейки в начало
    for _ in range(first_weekday):
        calendar_data.append({
            'date': None,
            'is_empty': True
        })
    
    # Добавляем дни месяца
    current_date = first_day
    while current_date <= last_day:
        day_transactions = Transaction.objects.filter(
            user=request.user,
            date=current_date
        ).select_related('category')
        
        day_payments = RegularPayment.objects.filter(
            user=request.user,
            next_payment_date=current_date
        )
        
        # Определяем цвет дня на основе транзакций
        day_color = '#f2f3fb'  # дефолтный цвет
        if day_transactions.exists():
            income = day_transactions.filter(type='income').aggregate(Sum('amount'))['amount__sum'] or 0
            expense = day_transactions.filter(type='expense').aggregate(Sum('amount'))['amount__sum'] or 0
            if income > expense:
                day_color = '#18dccb'
            elif expense > income:
                day_color = '#f87f0e'
            else:
                day_color = '#2f2cef'
        elif day_payments.exists():
            day_color = '#f60cf0'
            
        calendar_data.append({
            'date': current_date,
            'is_empty': False,
            'transactions': day_transactions,
            'regular_payments': day_payments,
            'color': day_color,
            'total_income': day_transactions.filter(type='income').aggregate(Sum('amount'))['amount__sum'] or 0,
            'total_expense': day_transactions.filter(type='expense').aggregate(Sum('amount'))['amount__sum'] or 0,
        })
        
        current_date += timedelta(days=1)
    
    # Добавляем пустые ячейки в конец до полной недели
    while len(calendar_data) % 7 != 0:
        calendar_data.append({
            'date': None,
            'is_empty': True
        })
    
    MONTHS_RU = {
        1: 'Январь', 2: 'Февраль', 3: 'Март', 4: 'Апрель',
        5: 'Май', 6: 'Июнь', 7: 'Июль', 8: 'Август',
        9: 'Сентябрь', 10: 'Октябрь', 11: 'Ноябрь', 12: 'Декабрь'
    }
    
    context = {
        'calendar_data': calendar_data,
        'year': year,
        'month': month,
        'month_name': f"{MONTHS_RU[month]} {year}",
        'prev_month': (first_day - timedelta(days=1)).strftime('%Y-%m'),
        'next_month': (last_day + timedelta(days=1)).strftime('%Y-%m'),
    }
    
    return render(request, 'operations/calendar.html', context)