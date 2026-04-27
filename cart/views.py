from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db import transaction

from orders.models import Order, OrderItem
from products.models import ProductInfo


class CartView(APIView):
    """
    Управление корзиной покупателя
    
    GET /api/v1/cart/ - просмотр корзины
    POST /api/v1/cart/ - добавить товар
    DELETE /api/v1/cart/<item_id>/ - удалить товар
    PATCH /api/v1/cart/<item_id>/ - изменить количество
    """
    permission_classes = [IsAuthenticated]
    
    def get_cart(self, user):
        """Получить или создать корзину пользователя"""
        cart, created = Order.objects.get_or_create(
            user=user,
            state='basket',
            defaults={'state': 'basket'}
        )
        return cart
    
    def get(self, request):
        """Просмотр корзины"""
        cart = self.get_cart(request.user)
        
        items = cart.ordered_items.select_related(
            'product_info__product', 
            'product_info__shop'
        ).all()
        
        cart_data = {
            'id': cart.id,
            'created_at': cart.dt,
            'items': [],
            'total_quantity': 0,
            'total_price': 0
        }
        
        total_price = 0
        total_quantity = 0
        
        for item in items:
            price = item.product_info.price
            subtotal = price * item.quantity
            total_price += subtotal
            total_quantity += item.quantity
            
            cart_data['items'].append({
                'id': item.id,
                'product_id': item.product_info.product.id,
                'product_name': item.product_info.product.name,
                'shop_id': item.product_info.shop.id,
                'shop_name': item.product_info.shop.name,
                'quantity': item.quantity,
                'price': price,
                'subtotal': subtotal
            })
        
        cart_data['total_quantity'] = total_quantity
        cart_data['total_price'] = total_price
        
        return Response(cart_data)
    
    def post(self, request):
        """
        Добавление товара в корзину
        
        {
            "product_info_id": 1,
            "quantity": 2
        }
        """
        product_info_id = request.data.get('product_info_id')
        quantity = request.data.get('quantity', 1)
        
        if not product_info_id:
            return Response({
                'Status': False, 
                'Error': 'Не указан product_info_id'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            quantity = int(quantity)
            if quantity <= 0:
                raise ValueError
        except ValueError:
            return Response({
                'Status': False, 
                'Error': 'Количество должно быть положительным числом'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Проверка существования товара
        try:
            product_info = ProductInfo.objects.select_related('shop').get(
                id=product_info_id,
                shop__state=True
            )
        except ProductInfo.DoesNotExist:
            return Response({
                'Status': False, 
                'Error': 'Товар не найден или магазин неактивен'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Проверка наличия
        if product_info.quantity < quantity:
            return Response({
                'Status': False, 
                'Error': f'Недостаточно товара. Доступно: {product_info.quantity}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        cart = self.get_cart(request.user)
        
        # Проверка, есть ли уже этот товар в корзине
        cart_item, created = OrderItem.objects.get_or_create(
            order=cart,
            product_info=product_info,
            defaults={'quantity': quantity}
        )
        
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
        
        return Response({
            'Status': True,
            'Message': f'Товар "{product_info.product.name}" добавлен в корзину',
            'Quantity': cart_item.quantity
        }, status=status.HTTP_201_CREATED)
    
    def delete(self, request, item_id=None):
        """Удаление товара из корзины"""
        cart = self.get_cart(request.user)
        
        try:
            if item_id:
                # Удаление конкретного товара
                cart_item = OrderItem.objects.get(order=cart, id=item_id)
                cart_item.delete()
                message = f'Товар "{cart_item.product_info.product.name}" удален из корзины'
            else:
                # Очистка всей корзины
                cart.ordered_items.all().delete()
                message = 'Корзина очищена'
        except OrderItem.DoesNotExist:
            return Response({
                'Status': False, 
                'Error': 'Товар не найден в корзине'
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({'Status': True, 'Message': message})
    
    def patch(self, request, item_id):
        """
        Изменение количества товара в корзине
        
        {
            "quantity": 5
        }
        """
        cart = self.get_cart(request.user)
        new_quantity = request.data.get('quantity')
        
        try:
            new_quantity = int(new_quantity)
            if new_quantity <= 0:
                raise ValueError
        except (ValueError, TypeError):
            return Response({
                'Status': False, 
                'Error': 'Количество должно быть положительным числом'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            cart_item = OrderItem.objects.select_related('product_info').get(
                order=cart, 
                id=item_id
            )
        except OrderItem.DoesNotExist:
            return Response({
                'Status': False, 
                'Error': 'Товар не найден в корзине'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Проверка наличия
        if cart_item.product_info.quantity < new_quantity:
            return Response({
                'Status': False, 
                'Error': f'Недостаточно товара. Доступно: {cart_item.product_info.quantity}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        cart_item.quantity = new_quantity
        cart_item.save()
        
        return Response({
            'Status': True,
            'Message': 'Количество обновлено',
            'Quantity': cart_item.quantity
        })