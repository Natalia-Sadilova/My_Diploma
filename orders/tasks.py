from celery import shared_task
from django.db import transaction
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


@shared_task
def process_order_confirmation(order_id):
    """
    Асинхронная обработка подтверждения заказа
    """
    from .models import Order
    
    try:
        with transaction.atomic():
            # Получаем заказ с нужными связями
            order = Order.objects.select_related('user', 'contact').get(id=order_id)
            
            # Получаем все позиции заказа через ordered_items
            items = order.ordered_items.select_related(
                'product_info__product', 
                'product_info__shop'
            ).all()
            
            # Проверяем, есть ли позиции
            if not items.exists():
                logger.warning(f"Order {order_id} has no items")
                return {'status': 'error', 'error': 'Заказ пуст'}
            
            # Проверяем наличие товаров
            for item in items:
                if item.product_info.quantity < item.quantity:
                    return {
                        'status': 'error', 
                        'error': f'Недостаточно товара: {item.product_info.product.name}'
                    }
            
            # Обновляем статус заказа
            order.state = 'confirmed'
            order.save()
            
            # Уменьшаем количество на складе
            for item in items:
                product_info = item.product_info
                product_info.quantity -= item.quantity
                product_info.save()
            
            # Формируем данные для email
            from users.tasks import send_order_confirmation_email, send_admin_notification_email
            
            order_data = {
                'id': order.id,
                'created_at': order.dt.isoformat(),
                'items': [
                    {
                        'name': item.product_info.product.name,
                        'quantity': item.quantity,
                        'price': float(item.product_info.price),
                        'subtotal': float(item.quantity * item.product_info.price)
                    }
                    for item in items
                ],
                'total': float(sum(item.quantity * item.product_info.price for item in items)),
                'contact': {
                    'city': order.contact.city,
                    'street': order.contact.street,
                    'house': order.contact.house,
                    'phone': order.contact.phone
                } if order.contact else None
            }
            
            # Отправляем письма асинхронно
            send_order_confirmation_email.delay(
                order_id=order.id,
                user_email=order.user.email,
                user_name=order.user.first_name or order.user.email,
                order_data=order_data
            )
            
            send_admin_notification_email.delay(
                order_id=order.id,
                admin_email=getattr(settings, 'ADMIN_EMAIL', settings.DEFAULT_FROM_EMAIL),
                order_summary=order_data
            )
            
            logger.info(f"Order {order_id} processed successfully")
            return {'status': 'success', 'order_id': order_id}
            
    except Order.DoesNotExist:
        logger.error(f"Order {order_id} not found")
        return {'status': 'error', 'error': 'Order not found'}
    except Exception as exc:
        logger.error(f"Failed to process order {order_id}: {exc}")
        return {'status': 'error', 'error': str(exc)}


@shared_task
def retry_failed_order_notifications():
    """Повторная отправка неудавшихся уведомлений о заказах"""
    from .models import Order
    
    orders = Order.objects.filter(state='pending_notification')
    
    results = []
    for order in orders:
        result = process_order_confirmation.delay(order.id)
        results.append({'order_id': order.id, 'task_id': result.id})
    
    logger.info(f"Retrying notifications for {len(orders)} orders")
    return results


@shared_task
def update_order_status(order_id, new_status):
    """
    Асинхронное обновление статуса заказа
    """
    from .models import Order
    
    try:
        order = Order.objects.get(id=order_id)
        old_status = order.state
        order.state = new_status
        order.save()
        
        if new_status == 'delivered':
            send_mail(
                subject=f'Ваш заказ #{order_id} доставлен',
                message=f'Заказ #{order_id} успешно доставлен. Спасибо за покупку!',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[order.user.email],
                fail_silently=True,
            )
        
        logger.info(f"Order {order_id} status updated from {old_status} to {new_status}")
        return {'status': 'success', 'old_status': old_status, 'new_status': new_status}
        
    except Order.DoesNotExist:
        logger.error(f"Order {order_id} not found")
        return {'status': 'error', 'error': 'Order not found'}