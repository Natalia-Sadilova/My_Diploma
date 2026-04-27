from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import User, ConfirmEmailToken


@receiver(post_save, sender=User)
def send_confirmation_email(sender, instance, created, **kwargs):
    if created and not instance.is_active:
        token, _ = ConfirmEmailToken.objects.get_or_create(user=instance)
        send_mail(
            subject='Подтверждение регистрации',
            message=f'Для подтверждения регистрации перейдите по ссылке: '
                    f'{settings.BASE_URL}/api/v1/users/auth/verify-email/?token={token.key}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[instance.email],
            fail_silently=False,
        )