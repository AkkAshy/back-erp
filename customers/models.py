# coding: utf-8
"""
Модели для управления покупателями (CRM).
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.utils.translation import gettext_lazy as _
from decimal import Decimal


class CustomerGroup(models.Model):
    """Группа покупателей"""
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    discount_percent = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    min_purchase_amount = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(0)]
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'customers_group'
        ordering = ['-discount_percent', 'name']
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['discount_percent']),
        ]

    def __str__(self):
        return f"{self.name} ({self.discount_percent}%)"

    @property
    def members_count(self):
        return self.customers.filter(is_active=True).count()


class Customer(models.Model):
    """Покупатель"""
    
    CUSTOMER_TYPE_CHOICES = [
        ('individual', 'Физическое лицо'),
        ('company', 'Юридическое лицо'),
    ]

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True)
    middle_name = models.CharField(max_length=100, blank=True)
    customer_type = models.CharField(max_length=20, choices=CUSTOMER_TYPE_CHOICES, default='individual')
    
    company_name = models.CharField(max_length=255, blank=True)
    tax_id = models.CharField(max_length=50, blank=True)
    
    phone_regex = RegexValidator(regex=r'^\+998\d{9}$')
    phone = models.CharField(validators=[phone_regex], max_length=13, unique=True)
    phone_2 = models.CharField(validators=[phone_regex], max_length=13, blank=True)
    email = models.EmailField(blank=True)
    
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    region = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    
    group = models.ForeignKey(
        CustomerGroup, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='customers'
    )
    
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    credit_limit = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        validators=[MinValueValidator(0)]
    )
    
    loyalty_points = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    total_purchases = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        validators=[MinValueValidator(0)]
    )
    total_purchases_count = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    
    birthday = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    is_active = models.BooleanField(default=True)
    is_blocked = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_purchase_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'customers_customer'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['phone']),
            models.Index(fields=['email']),
            models.Index(fields=['group']),
            models.Index(fields=['is_active', 'is_blocked']),
            models.Index(fields=['last_name', 'first_name']),
            models.Index(fields=['company_name']),
            models.Index(fields=['last_purchase_at']),
        ]

    def __str__(self):
        if self.customer_type == 'company' and self.company_name:
            return f"{self.company_name} ({self.phone})"
        return f"{self.get_full_name()} ({self.phone})"

    @property
    def full_name(self):
        return self.get_full_name()

    def get_full_name(self):
        parts = [self.last_name, self.first_name, self.middle_name]
        return ' '.join(filter(None, parts)) or self.phone

    @property
    def available_credit(self):
        if self.is_blocked:
            return Decimal('0.00')
        return self.credit_limit - abs(min(self.balance, Decimal('0.00')))

    @property
    def is_vip(self):
        return self.group and self.group.discount_percent >= 10

    @property
    def default_discount(self):
        return self.group.discount_percent if self.group else Decimal('0.00')

    def add_purchase(self, amount):
        from django.utils import timezone
        self.total_purchases += amount
        self.total_purchases_count += 1
        self.last_purchase_at = timezone.now()
        points = int(amount / 100)
        self.loyalty_points += points
        self.save()

    def add_payment(self, amount):
        self.balance += amount
        self.save()

    def charge(self, amount):
        if amount > self.available_credit + self.balance:
            raise ValueError(f'Недостаточно средств. Доступно: {self.available_credit + self.balance}')
        self.balance -= amount
        self.save()


class CustomerTransaction(models.Model):
    """Транзакция покупателя"""
    
    TRANSACTION_TYPE_CHOICES = [
        ('payment', 'Платёж'),
        ('charge', 'Списание'),
        ('bonus_accrual', 'Начисление бонусов'),
        ('bonus_redemption', 'Списание бонусов'),
        ('correction', 'Корректировка'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    balance_before = models.DecimalField(max_digits=12, decimal_places=2)
    balance_after = models.DecimalField(max_digits=12, decimal_places=2)
    sale = models.ForeignKey('sales.Sale', on_delete=models.SET_NULL, null=True, blank=True, related_name='customer_transactions')
    description = models.TextField(blank=True)
    performed_by = models.ForeignKey(
        'users.Employee',
        on_delete=models.SET_NULL,
        null=True,
        related_name='customer_transactions',
        verbose_name='Выполнил'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'customers_transaction'
        ordering = ['-created_at']
        indexes = [            models.Index(fields=['customer', 'created_at']),
            models.Index(fields=['transaction_type']),
            models.Index(fields=['sale']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        sign = '+' if self.amount >= 0 else ''
        return f"{self.customer.get_full_name()} - {sign}{self.amount} ({self.get_transaction_type_display()})"

    def save(self, *args, **kwargs):
        if not self.pk:
            self.balance_before = self.customer.balance
            if self.transaction_type == 'payment':
                self.customer.balance += self.amount
            elif self.transaction_type == 'charge':
                self.customer.balance -= self.amount
            self.balance_after = self.customer.balance
            self.customer.save()
        super().save(*args, **kwargs)
