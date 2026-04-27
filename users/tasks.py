from celery import shared_task
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=settings.EMAIL_MAX_RETRIES, default_retry_delay=settings.EMAIL_RETRY_DELAY)
def send_email_task(self, subject, message, recipient_list, html_message=None, from_email=None):
    """
    Асинхронная отправка email
    
    Args:
        subject: Тема письма
        message: Текстовое сообщение
        recipient_list: Список получателей
        html_message: HTML версия сообщения
        from_email: Отправитель
    """
    try:
        if not from_email:
            from_email = settings.DEFAULT_FROM_EMAIL
        
        if html_message:
            # Отправляем HTML письмо
            email = EmailMultiAlternatives(
                subject=subject,
                body=message,
                from_email=from_email,
                to=recipient_list
            )
            email.attach_alternative(html_message, "text/html")
            email.send()
        else:
            # Отправляем обычное письмо
            send_mail(
                subject=subject,
                message=message,
                from_email=from_email,
                recipient_list=recipient_list,
                fail_silently=False,
            )
        
        logger.info(f"Email sent successfully to {recipient_list}")
        return {'status': 'success', 'recipients': recipient_list}
        
    except Exception as exc:
        logger.error(f"Email sending failed: {exc}")
        # Повторяем задачу при ошибке
        raise self.retry(exc=exc, countdown=60)


@shared_task
def send_order_confirmation_email(order_id, user_email, user_name, order_data):
    """
    Отправка подтверждения заказа клиенту
    
    Args:
        order_id: ID заказа
        user_email: Email клиента
        user_name: Имя клиента
        order_data: Данные заказа
    """
    subject = f'Подтверждение заказа #{order_id}'
    
    # Рендерим HTML шаблон
    html_message = render_to_string('email/order_confirmation.html', {
        'order_id': order_id,
        'user_name': user_name,
        'order_data': order_data,
        'site_url': settings.BASE_URL
    })
    
    plain_message = strip_tags(html_message)
    
    return send_email_task.delay(
        subject=subject,
        message=plain_message,
        recipient_list=[user_email],
        html_message=html_message
    )


@shared_task
def send_admin_notification_email(order_id, admin_email, order_summary):
    """
    Отправка уведомления администратору о новом заказе
    
    Args:
        order_id: ID заказа
        admin_email: Email администратора
        order_summary: Сводка заказа
    """
    subject = f'Новый заказ #{order_id}'
    
    html_message = render_to_string('email/admin_notification.html', {
        'order_id': order_id,
        'order_summary': order_summary,
        'admin_url': f"{settings.BASE_URL}/admin/orders/order/{order_id}/change/"
    })
    
    plain_message = strip_tags(html_message)
    
    return send_email_task.delay(
        subject=subject,
        message=plain_message,
        recipient_list=[admin_email],
        html_message=html_message
    )


@shared_task
def send_verification_email(user_id, user_email, verification_token):
    """
    Отправка письма для подтверждения email
    
    Args:
        user_id: ID пользователя
        user_email: Email пользователя
        verification_token: Токен подтверждения
    """
    subject = 'Подтверждение регистрации'
    
    verification_url = f"{settings.BASE_URL}/api/v1/users/verify-email/?token={verification_token}"
    
    html_message = render_to_string('email/verification.html', {
        'verification_url': verification_url,
        'user_id': user_id
    })
    
    plain_message = f"Для подтверждения регистрации перейдите по ссылке: {verification_url}"
    
    return send_email_task.delay(
        subject=subject,
        message=plain_message,
        recipient_list=[user_email],
        html_message=html_message
    )


@shared_task
def send_password_reset_email(user_email, reset_token):
    """
    Отправка письма для сброса пароля
    
    Args:
        user_email: Email пользователя
        reset_token: Токен сброса пароля
    """
    subject = 'Сброс пароля'
    
    reset_url = f"{settings.BASE_URL}/api/v1/users/password-reset-confirm/?token={reset_token}"
    
    html_message = render_to_string('email/password_reset.html', {
        'reset_url': reset_url,
        'user_email': user_email
    })
    
    plain_message = f"Для сброса пароля перейдите по ссылке: {reset_url}"
    
    return send_email_task.delay(
        subject=subject,
        message=plain_message,
        recipient_list=[user_email],
        html_message=html_message
    )


@shared_task
def cleanup_expired_tokens():
    """Очистка просроченных токенов подтверждения"""
    from datetime import timedelta
    from django.utils import timezone
    from users.models import ConfirmEmailToken
    
    # Удаляем токены старше 24 часов
    expiration_time = timezone.now() - timedelta(hours=24)
    deleted_count = ConfirmEmailToken.objects.filter(created_at__lt=expiration_time).delete()[0]
    
    logger.info(f"Cleaned up {deleted_count} expired confirmation tokens")
    return {'deleted_tokens': deleted_count}