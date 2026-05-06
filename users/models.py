from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_rest_passwordreset.tokens import get_token_generator

USER_TYPE_CHOICES = (
    ('shop', 'Магазин'),
    ('buyer', 'Покупатель'),
)


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('Данный адрес электронной почты должен быть установлен')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Создание обычного пользователя"""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        extra_fields.setdefault('is_active', False)  # Обычный пользователь требует подтверждения email
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """
        Создание суперпользователя
        Суперпользователь создается активным и имеет полные права
        """
        # Устанавливаем значения по умолчанию для суперпользователя
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True) 
        
        # Дополнительные поля для суперпользователя
        extra_fields.setdefault('type', 'buyer')  
        
        # Проверки корректности
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Суперпользователь должен иметь is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Суперпользователь должен иметь is_superuser=True.')
        if extra_fields.get('is_active') is not True:
            raise ValueError('Суперпользователь должен иметь is_active=True.')

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Стандартная модель пользователей"""
    REQUIRED_FIELDS = []
    objects = UserManager()
    USERNAME_FIELD = 'email'
    
    email = models.EmailField(_('email address'), unique=True)
    company = models.CharField(verbose_name='Компания', max_length=40, blank=True)
    position = models.CharField(verbose_name='Должность', max_length=40, blank=True)
    username_validator = UnicodeUsernameValidator()
    username = models.CharField(
        _('username'),
        max_length=150,
        help_text=_('Требуется 150 символов или меньше. Буквы, цифры и @/./+/-/_ only.'),
        validators=[username_validator],
        error_messages={
            'unique': _("Пользователь с таким именем уже существует."),
        },
        blank=True,  
        default='', 
    )
    is_active = models.BooleanField(
        _('active'),
        default=False,  
        help_text=_(
            'Определяет, следует ли считать этого пользователя активным. '
            'Отмените выбор вместо удаления аккаунтов.'
        ),
    )
    is_verified = models.BooleanField(
        default=False,
        verbose_name='Email подтверждён',
        help_text='Пользователь подтвердил свой email'
    )
    type = models.CharField(
        verbose_name='Тип пользователя', 
        choices=USER_TYPE_CHOICES, 
        max_length=5, 
        default='buyer'
    )

    def __str__(self):
        if self.first_name or self.last_name:
            return f'{self.first_name} {self.last_name}'.strip()
        return self.email

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = "Список пользователей"
        ordering = ('email',)


class ConfirmEmailToken(models.Model):
    """Токен подтверждения Email"""
    class Meta:
        verbose_name = 'Токен подтверждения Email'
        verbose_name_plural = 'Токены подтверждения Email'

    @staticmethod
    def generate_key():
        return get_token_generator().generate_token()

    user = models.ForeignKey(
        User,
        related_name='confirm_email_tokens',
        on_delete=models.CASCADE,
        verbose_name=_("Пользователь, связанный с этим токеном")
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Дата создания токена")
    )

    key = models.CharField(
        _("Ключ"),
        max_length=64,
        db_index=True,
        unique=True
    )

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_key()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"Токен подтверждения для пользователя {self.user.email}"