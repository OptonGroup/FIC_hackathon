from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date

class Credit(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    name = models.CharField(max_length=100, verbose_name='Название')
    bank = models.CharField(max_length=100, verbose_name='Банк', default=None)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Сумма кредита', default=0)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Выплачено')
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='Процентная ставка')
    end_date = models.DateField(verbose_name='Дата окончания')
    
    def get_progress_percentage(self):
        """Возвращает процент выплаты кредита"""
        if self.total_amount:
            return min(round((self.paid_amount / self.total_amount) * 100, 1), 100)
        return 0
    
    class Meta:
        verbose_name = 'Кредит'
        verbose_name_plural = 'Кредиты'
        
    def __str__(self):
        return f"{self.name} ({self.bank})"

class Target(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    name = models.CharField(max_length=100, verbose_name='Название')
    target_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Целевая сумма')
    current_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Текущая сумма')
    deadline = models.DateField(verbose_name='Срок достижения')
    created_at = models.DateField(default=date.today, verbose_name='Дата создания')
    
    def get_progress_percentage(self):
        """Возвращает процент выполнения цели с учетом времени"""
        if self.target_amount <= 0:
            return 0
            
        # Расчет финансового прогресса
        financial_progress = (self.current_amount / self.target_amount) * 100
        
        # Расчет временного прогресса
        total_days = (self.deadline - self.created_at).days
        days_passed = (date.today() - self.created_at).days
        
        if total_days <= 0:
            return min(round(financial_progress, 1), 100)
            
        time_progress = (days_passed / total_days) * 100
        
        # Если времени прошло больше, чем денег накоплено - красный статус
        if time_progress > financial_progress:
            return min(round(time_progress, 1), 100)
        
        return min(round(financial_progress, 1), 100)
    
    def get_status(self):
        """Возвращает статус цели"""
        financial_progress = (self.current_amount / self.target_amount) * 100 if self.target_amount else 0
        total_days = (self.deadline - self.created_at).days
        days_passed = (date.today() - self.created_at).days
        time_progress = (days_passed / total_days) * 100 if total_days > 0 else 0
        
        if financial_progress >= 100:
            return 'success'  # Цель достигнута
        elif time_progress > financial_progress:
            return 'danger'   # Отстаем от графика
        elif time_progress > financial_progress - 10:
            return 'warning'  # Небольшое отставание
        else:
            return 'info'     # Идем по графику или с опережением
    
    class Meta:
        verbose_name = 'Цель'
        verbose_name_plural = 'Цели'
        
    def __str__(self):
        return self.name

class Category(models.Model):
    CATEGORY_TYPES = [
        ('income', 'Доход'),
        ('expense', 'Расход'),
        ('both', 'Обе'),
    ]

    DEFAULT_CATEGORIES = {
        'income': [
            ('salary', 'Зарплата', 'bi-cash', '#28a745'),
            ('investment', 'Инвестиции', 'bi-graph-up', '#17a2b8'),
            ('gift', 'Подарки', 'bi-gift', '#dc3545'),
            ('other_income', 'Прочие доходы', 'bi-plus-circle', '#6c757d'),
        ],
        'expense': [
            ('food', 'Продукты', 'bi-cart', '#fd7e14'),
            ('transport', 'Транспорт', 'bi-car-front', '#6610f2'),
            ('housing', 'Жилье', 'bi-house', '#e83e8c'),
            ('utilities', 'Коммунальные услуги', 'bi-water', '#20c997'),
            ('entertainment', 'Развлечения', 'bi-controller', '#ffc107'),
            ('health', 'Здоровье', 'bi-heart-pulse', '#dc3545'),
            ('shopping', 'Покупки', 'bi-bag', '#0dcaf0'),
            ('education', 'Образование', 'bi-book', '#6f42c1'),
            ('other_expense', 'Прочие расходы', 'bi-three-dots', '#6c757d'),
        ]
    }
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    name = models.CharField(max_length=50, verbose_name='Название')
    type = models.CharField(
        max_length=7, 
        choices=CATEGORY_TYPES, 
        default='both',
        verbose_name='Тип категории'
    )
    icon = models.CharField(
        max_length=50, 
        default='bi-tag',
        verbose_name='Иконка'
    )
    color = models.CharField(
        max_length=7, 
        default='#6c757d',
        verbose_name='Цвет'
    )
    
    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['name']
        unique_together = ['user', 'name']  # Имя категории должно быть уникальным для пользователя
        
    def __str__(self):
        return self.name

    @classmethod
    def create_default_categories(cls, user):
        for category_type, categories in cls.DEFAULT_CATEGORIES.items():
            for code, name, icon, color in categories:
                cls.objects.get_or_create(
                    user=user,
                    name=name,
                    defaults={
                        'type': category_type,
                        'icon': icon,
                        'color': color
                    }
                )

class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('income', 'Доход'),
        ('expense', 'Расход'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    type = models.CharField(max_length=7, choices=TRANSACTION_TYPES, verbose_name='Тип')
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Сумма')
    category = models.ForeignKey(
        Category, 
        on_delete=models.PROTECT,  # Защищаем от удаления используемых категорий
        verbose_name='Категория'
    )
    description = models.TextField(blank=True, verbose_name='Описание')
    date = models.DateField(verbose_name='Дата')
    credit = models.ForeignKey(Credit, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Кредит')
    target = models.ForeignKey(Target, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Цель')
    
    class Meta:
        verbose_name = 'Транзакция'
        verbose_name_plural = 'Транзакции'
        
    def __str__(self):
        return f"{self.get_type_display()} - {self.amount}"

class RegularPayment(models.Model):
    FREQUENCY_CHOICES = [
        ('weekly', 'Еженедельно'),
        ('monthly', 'Ежемесячно'),
        ('yearly', 'Ежегодно'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    name = models.CharField(max_length=100, verbose_name='Название')
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Сумма')
    category = models.ForeignKey('Category', on_delete=models.CASCADE, verbose_name='Категория', null=True)
    frequency = models.CharField(max_length=10, choices=FREQUENCY_CHOICES, verbose_name='Частота')
    next_payment_date = models.DateField(verbose_name='Следующий платеж', null=True)
    description = models.TextField(blank=True, verbose_name='Описание')
    
    class Meta:
        verbose_name = 'Регулярный платеж'
        verbose_name_plural = 'Регулярные платежи'
        ordering = ['next_payment_date']
        
    def __str__(self):
        return self.name
