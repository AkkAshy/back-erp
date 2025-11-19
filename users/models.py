"""
Users app models: Store, Employee
Multi-tenant architecture with JWT-based authentication
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)


class Store(models.Model):
    """
    Магазин - основная единица мультитенантности.
    Один владелец может иметь N магазинов.
    Каждый магазин изолирован по данным через JWT и схемы PostgreSQL.
    """

    # Основная информация
    name = models.CharField(
        max_length=255,
        verbose_name=_('Название магазина'),
        help_text=_('Название магазина или компании')
    )

    slug = models.SlugField(
        max_length=100,
        unique=True,
        verbose_name=_('Слаг'),
        help_text=_('Используется для PostgreSQL схемы: store_{slug}')
    )

    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Описание'),
        help_text=_('Описание деятельности магазина')
    )

    # Контактная информация
    address = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Адрес'),
        help_text=_('Физический адрес магазина')
    )

    city = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_('Город')
    )

    region = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_('Область/Регион')
    )

    phone_regex = RegexValidator(
        regex=r'^\+998\d{9}$',
        message=_('Номер телефона должен быть в формате: +998XXXXXXXXX')
    )

    phone = models.CharField(
        validators=[phone_regex],
        max_length=13,
        blank=True,
        null=True,
        verbose_name=_('Телефон'),
        help_text=_('Формат: +998XXXXXXXXX')
    )

    email = models.EmailField(
        blank=True,
        null=True,
        verbose_name=_('Email')
    )

    # Юридические данные
    legal_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_('Юридическое название'),
        help_text=_('Официальное название организации')
    )

    tax_id = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name=_('ИНН'),
        help_text=_('Идентификационный номер налогоплательщика')
    )

    # Технические поля для мультитенантности
    tenant_key = models.CharField(
        max_length=100,
        unique=True,
        editable=False,
        db_index=True,
        verbose_name=_('Ключ арендатора'),
        help_text=_('Уникальный ключ для идентификации магазина в запросах (X-Tenant-Key)')
    )

    schema_name = models.CharField(
        max_length=63,
        unique=True,
        editable=False,
        verbose_name=_('Имя схемы PostgreSQL'),
        help_text=_('Автоматически генерируется: tenant_{slug}')
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Активен'),
        help_text=_('Неактивные магазины не могут входить в систему')
    )

    # Метаданные
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Дата создания')
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Дата обновления')
    )

    # Владелец магазина
    owner = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='owned_stores',
        verbose_name=_('Владелец'),
        help_text=_('Пользователь, создавший магазин')
    )

    class Meta:
        verbose_name = _('Магазин')
        verbose_name_plural = _('Магазины')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['tenant_key']),  # Для быстрого поиска по ключу
            models.Index(fields=['is_active']),
            models.Index(fields=['owner']),
        ]

    def __str__(self):
        return f"{self.name} ({self.slug})"

    def save(self, *args, **kwargs):
        """Автоматически генерируем tenant_key и schema_name"""
        import uuid
        import hashlib

        # Генерируем уникальный tenant_key
        if not self.tenant_key:
            # Формат: slug_короткий_хеш (например: tokyo_34b12fa)
            unique_string = f"{self.slug}_{uuid.uuid4().hex}"
            short_hash = hashlib.md5(unique_string.encode()).hexdigest()[:8]
            self.tenant_key = f"{self.slug}_{short_hash}"

        # Генерируем schema_name
        if not self.schema_name:
            self.schema_name = f"tenant_{self.slug}"

        super().save(*args, **kwargs)

    def clean(self):
        """Валидация перед сохранением"""
        super().clean()

        # Проверка slug на допустимые символы для PostgreSQL schema
        if self.slug:
            if not self.slug.replace('_', '').isalnum():
                raise ValidationError({
                    'slug': _('Слаг может содержать только буквы, цифры и подчеркивание')
                })

            # PostgreSQL schemas не могут начинаться с цифры
            if self.slug[0].isdigit():
                raise ValidationError({
                    'slug': _('Слаг не может начинаться с цифры')
                })

    @property
    def employee_count(self):
        """Количество сотрудников в магазине"""
        return self.employees.count()

    @property
    def active_employee_count(self):
        """Количество активных сотрудников"""
        return self.employees.filter(is_active=True).count()


class Employee(models.Model):
    """
    Сотрудник - связь между User и Store с ролью.
    Один пользователь может работать в нескольких магазинах с разными ролями.
    """

    # Роли сотрудников
    class Role(models.TextChoices):
        OWNER = 'owner', _('Владелец')
        MANAGER = 'manager', _('Менеджер')
        CASHIER = 'cashier', _('Кассир')
        STOCKKEEPER = 'stockkeeper', _('Складчик')
        STAFF = 'staff', _('Общий аккаунт сотрудников')

    # Пол сотрудника
    class Sex(models.TextChoices):
        MALE = 'male', _('Мужской')
        FEMALE = 'female', _('Женский')

    # Основные связи
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='employments',
        verbose_name=_('Пользователь'),
        null=True,
        blank=True,
        help_text=_('Опционально. Для кассиров без аккаунта можно оставить пустым')
    )

    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        related_name='employees',
        verbose_name=_('Магазин')
    )

    # Роль в магазине
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CASHIER,
        verbose_name=_('Роль'),
        help_text=_('Роль сотрудника в магазине')
    )

    # Личные данные (для кассиров без user аккаунта)
    first_name = models.CharField(
        max_length=150,
        blank=True,
        verbose_name=_('Имя'),
        help_text=_('Имя сотрудника. Используется если нет user аккаунта')
    )

    last_name = models.CharField(
        max_length=150,
        blank=True,
        verbose_name=_('Фамилия'),
        help_text=_('Фамилия сотрудника. Используется если нет user аккаунта')
    )

    # Контактная информация
    phone_regex = RegexValidator(
        regex=r'^\+998\d{9}$',
        message=_('Номер телефона должен быть в формате: +998XXXXXXXXX')
    )

    phone = models.CharField(
        validators=[phone_regex],
        max_length=13,
        blank=True,
        null=True,
        verbose_name=_('Телефон'),
        help_text=_('Личный телефон сотрудника')
    )

    # Дополнительная информация
    photo = models.ImageField(
        upload_to='employee_photos/',
        blank=True,
        null=True,
        verbose_name=_('Фото')
    )

    position = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_('Должность'),
        help_text=_('Дополнительное описание должности')
    )

    sex = models.CharField(
        max_length=10,
        choices=Sex.choices,
        blank=True,
        null=True,
        verbose_name=_('Пол'),
        help_text=_('Пол сотрудника')
    )

    # Статус
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Активен'),
        help_text=_('Неактивные сотрудники не могут входить в систему')
    )

    # Даты
    hired_at = models.DateField(
        auto_now_add=True,
        verbose_name=_('Дата найма')
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Дата создания записи')
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Дата обновления')
    )

    class Meta:
        verbose_name = _('Сотрудник')
        verbose_name_plural = _('Сотрудники')
        ordering = ['-created_at']
        # Убрали unique_together т.к. user теперь может быть NULL
        indexes = [
            models.Index(fields=['user', 'store']),
            models.Index(fields=['role']),
            models.Index(fields=['is_active']),
        ]
        constraints = [
            # Если есть user, то должна быть уникальная комбинация user+store
            models.UniqueConstraint(
                fields=['user', 'store'],
                condition=models.Q(user__isnull=False),
                name='unique_user_store'
            )
        ]

    def __str__(self):
        return f"{self.full_name} - {self.store.name} ({self.get_role_display()})"

    @property
    def full_name(self):
        """Возвращает полное имя сотрудника"""
        if self.user:
            return self.user.get_full_name() or self.user.username
        elif self.first_name or self.last_name:
            return f"{self.last_name} {self.first_name}".strip()
        else:
            return f"Сотрудник #{self.id}"

    def clean(self):
        """Валидация перед сохранением"""
        super().clean()

        # Валидация: должен быть либо user, либо first_name
        if not self.user and not self.first_name:
            raise ValidationError({
                'first_name': _('Укажите либо user аккаунт, либо имя сотрудника')
            })

        # Проверка: в магазине может быть только один владелец
        if self.role == self.Role.OWNER:
            existing_owner = Employee.objects.filter(
                store=self.store,
                role=self.Role.OWNER
            ).exclude(pk=self.pk).first()

            if existing_owner:
                raise ValidationError({
                    'role': _(f'В магазине уже есть владелец: {existing_owner.full_name}')
                })

    @property
    def permissions(self):
        """
        Получить разрешения на основе роли.
        Возвращает список разрешений для использования в JWT.
        """
        permissions_map = {
            self.Role.OWNER: [
                'view_all', 'create_all', 'update_all', 'delete_all',
                'manage_employees', 'manage_store', 'view_analytics',
                'manage_products', 'manage_sales', 'manage_customers'
            ],
            self.Role.MANAGER: [
                'view_all', 'create_all', 'update_all',
                'manage_products', 'manage_sales', 'manage_customers',
                'view_analytics'
            ],
            self.Role.CASHIER: [
                'view_products', 'create_sales', 'view_customers',
                'create_customers'
            ],
            self.Role.STOCKKEEPER: [
                'view_products', 'create_products', 'update_products',
                'manage_inventory', 'view_analytics'
            ],
            self.Role.STAFF: [
                'view_products', 'create_sales', 'view_customers',
                'create_customers', 'update_products', 'manage_inventory'
            ],
        }
        return permissions_map.get(self.role, [])

    def has_permission(self, permission):
        """Проверка наличия разрешения"""
        return permission in self.permissions


# Сигналы для автоматических действий

from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=Employee)
def update_user_groups(sender, instance, created, **kwargs):
    """
    Автоматически обновляем группы пользователя при изменении роли.
    Это нужно для работы с Django admin и permissions.
    """
    from django.contrib.auth.models import Group

    # Если у Employee нет user (кассир без аккаунта), пропускаем
    if not instance.user:
        return

    try:
        # Получаем или создаем группу по названию роли
        group, _ = Group.objects.get_or_create(name=instance.role)

        # Добавляем пользователя в группу
        instance.user.groups.add(group)

        # Если это владелец, даём права staff
        if instance.role == Employee.Role.OWNER:
            instance.user.is_staff = True
            instance.user.save(update_fields=['is_staff'])

        logger.info(f"Updated groups for user {instance.user.username}: {instance.role}")

    except Exception as e:
        logger.error(f"Error updating user groups: {e}")


@receiver(post_save, sender=Store)
def create_owner_employee(sender, instance, created, **kwargs):
    """
    Автоматически создаём запись Employee с ролью OWNER
    и общий аккаунт STAFF для всех сотрудников при создании нового магазина.
    """
    if created:
        try:
            # 1. Создаём Employee для владельца
            Employee.objects.create(
                user=instance.owner,
                store=instance,
                role=Employee.Role.OWNER
            )
            logger.info(f"Created owner employee for store: {instance.name}")

            # 2. Создаём общий аккаунт для сотрудников (кассиров/складчиков)
            staff_username = f"{instance.slug}_staff"
            staff_password = "12345678"

            # Проверяем, не существует ли уже такой username
            if not User.objects.filter(username=staff_username).exists():
                staff_user = User.objects.create_user(
                    username=staff_username,
                    password=staff_password,
                    first_name="Сотрудники",
                    last_name=instance.name,
                    is_active=True
                )

                # Создаём Employee запись для этого общего аккаунта
                Employee.objects.create(
                    user=staff_user,
                    store=instance,
                    role=Employee.Role.STAFF,
                    first_name="Сотрудники",
                    last_name=instance.name
                )

                logger.info(
                    f"Created staff account for store: {instance.name}, "
                    f"username: {staff_username}, password: {staff_password}"
                )
            else:
                logger.warning(f"Staff username {staff_username} already exists, skipping creation")

        except Exception as e:
            logger.error(f"Error creating owner/staff employee: {e}")
