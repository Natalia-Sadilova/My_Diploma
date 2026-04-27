from rest_framework.views import APIView
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db import transaction
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from .models import Contact, Order, OrderItem
from .serializers import ContactSerializer, OrderSerializer, OrderDetailSerializer
from products.models import ProductInfo


class ContactListCreateView(generics.ListCreateAPIView):
    """
    Список и создание контактов (адресов доставки)
    
    GET /api/v1/orders/contacts/ - список контактов
    POST /api/v1/orders/contacts/ - создать контакт
    
    POST данные:
    {
        "city": "Москва",
        "street": "Тверская",
        "house": "15",
        "apartment": "45",
        "phone": "+79991234567"
    }
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ContactSerializer
    
    def get_queryset(self):
        return Contact.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ContactDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Просмотр, редактирование, удаление контакта
    
    GET /api/v1/orders/contacts/<id>/
    PUT /api/v1/orders/contacts/<id>/
    DELETE /api/v1/orders/contacts/<id>/
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ContactSerializer
    
    def get_queryset(self):
        return Contact.objects.filter(user=self.request.user)


class OrderListView(generics.ListAPIView):
    """
    Список заказов пользователя
    
    GET /api/v1/orders/
    """
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer
    
    def get_queryset(self):
        return Order.objects.filter(
            user=self.request.user
        ).exclude(state='basket').order_by('-dt')


class OrderDetailView(generics.RetrieveAPIView):
    """
    Детальная информация о заказе
    
    GET /api/v1/orders/<id>/
    """
    permission_classes = [IsAuthenticated]
    serializer_class = OrderDetailSerializer
    
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).exclude(state='basket')


class ConfirmOrderView(APIView):
    """
    Подтверждение заказа (оформление из корзины)
    
    POST /api/v1/orders/confirm/
    {
        "contact_id": 1
    }
    """
    permission_classes = [IsAuthenticated]
    
    @transaction.atomic
    def post(self, request):
        user = request.user
        contact_id = request.data.get('contact_id')
        
        # Проверка контакта
        if not contact_id:
            return Response({
                'Status': False, 
                'Error': 'Не указан контакт для доставки'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            contact = Contact.objects.get(id=contact_id, user=user)
        except Contact.DoesNotExist:
            return Response({
                'Status': False, 
                'Error': 'Контакт не найден'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Получаем корзину
        try:
            cart = Order.objects.get(user=user, state='basket')
        except Order.DoesNotExist:
            return Response({
                'Status': False, 
                'Error': 'Корзина пуста'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Проверяем, что корзина не пуста
        cart_items = cart.ordered_items.select_related(
            'product_info__product', 
            'product_info__shop'
        ).all()
        
        if not cart_items:
            return Response({
                'Status': False, 
                'Error': 'Корзина пуста'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Проверяем наличие товаров
        for item in cart_items:
            if item.product_info.quantity < item.quantity:
                return Response({
                    'Status': False,
                    'Error': f'Недостаточно товара "{item.product_info.product.name}". Доступно: {item.product_info.quantity}'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Обновляем статус корзины на "новый заказ"
        cart.state = 'new'
        cart.contact = contact
        cart.save()
        
        # Уменьшаем количество товаров на складе
        for item in cart_items:
            product_info = item.product_info
            product_info.quantity -= item.quantity
            product_info.save()
        
        # Отправляем email с подтверждением
        self.send_order_confirmation_email(user, cart, cart_items, contact)
        
        return Response({
            'Status': True,
            'Message': 'Заказ успешно оформлен',
            'OrderId': cart.id
        }, status=status.HTTP_201_CREATED)
    
    def send_order_confirmation_email(self, user, order, items, contact):
        """Отправка подтверждения заказа клиенту"""
        subject = f'Подтверждение заказа #{order.id}'
        
        # Формируем таблицу товаров
        items_html = ""
        total = 0
        for item in items:
            subtotal = item.product_info.price * item.quantity
            total += subtotal
            items_html += f"""
                <tr>
                    <td>{item.product_info.product.name}</td>
                    <td>{item.quantity}</td>
                    <td>{item.product_info.price} руб.</td>
                    <td>{subtotal} руб.</td>
                </tr>
            """
        
        html_message = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .total {{ font-weight: bold; }}
            </style>
        </head>
        <body>
            <h2>Здравствуйте, {user.first_name or user.email}!</h2>
            <p>Ваш заказ #{order.id} успешно оформлен.</p>
            
            <h3>Детали заказа:</h3>
            <table>
                <tr>
                    <th>Товар</th>
                    <th>Количество</th>
                    <th>Цена</th>
                    <th>Сумма</th>
                </tr>
                {items_html}
                <tr class="total">
                    <td colspan="3"><strong>Итого:</strong></td>
                    <td><strong>{total} руб.</strong></td>
                </tr>
            </table>
            
            <h3>Адрес доставки:</h3>
            <p>
                {contact.city}, {contact.street}, д.{contact.house}
                {f', кв.{contact.apartment}' if contact.apartment else ''}<br>
                Телефон: {contact.phone}
            </p>
            
            <p>Спасибо за покупку!</p>
            <hr>
            <small>Это письмо создано автоматически, пожалуйста, не отвечайте на него.</small>
        </body>
        </html>
        """
        
        plain_message = strip_tags(html_message)
        
        try:
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False
            )
        except Exception as e:
            print(f"Email sending error: {e}")
    
    def send_admin_notification_email(self, order, items, contact):
        """Отправка уведомления администратору (опционально)"""
        subject = f'Новый заказ #{order.id}'
        
        items_text = "\n".join([
            f"  - {item.product_info.product.name}: {item.quantity} x {item.product_info.price} = {item.product_info.price * item.quantity} руб."
            for item in items
        ])
        
        message = f"""
        Поступил новый заказ #{order.id}
        
        Покупатель: {order.user.email}
        Телефон: {contact.phone}
        Адрес: {contact.city}, {contact.street}, {contact.house}
        
        Товары:
        {items_text}
        
        Общая сумма: {sum(item.product_info.price * item.quantity for item in items)} руб.
        """
        
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[getattr(settings, 'ADMIN_EMAIL', settings.DEFAULT_FROM_EMAIL)],
                fail_silently=False
            )
        except Exception as e:
            print(f"Admin email error: {e}")