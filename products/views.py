from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from django.db import transaction
import yaml
import json

from .services import ProductImportService
from shops.models import Shop
from .models import Category, Product, ProductInfo
from .serializers import CategorySerializer, ProductSerializer, ProductInfoSerializer


class PartnerUpdate(APIView):
    """
    API для обновления прайса от поставщика (магазина)
    
    Поддерживает:
    - Загрузку файла (YAML или JSON)
    - Импорт по URL
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request, *args, **kwargs):
        # Проверка авторизации
        if not request.user.is_authenticated:
            return Response(
                {'Status': False, 'Error': 'Требуется авторизация'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Проверка типа пользователя (только для магазинов)
        if request.user.type != 'shop':
            return Response(
                {'Status': False, 'Error': 'Только для магазинов'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Проверяем, есть ли у пользователя магазин
        try:
            shop = Shop.objects.get(user=request.user)
            shop_id = shop.id
        except Shop.DoesNotExist:
            return Response(
                {'Status': False, 'Error': 'У вас не зарегистрирован магазин. Создайте магазин через админку.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        data = None
        
        # Вариант 1: Импорт по URL
        url = request.data.get('url')
        if url:
            try:
                validator = URLValidator()
                validator(url)
                data = ProductImportService.load_yaml_from_url(url)
            except ValidationError as e:
                return Response({'Status': False, 'Error': f'Некорректный URL: {str(e)}'})
            except Exception as e:
                return Response({'Status': False, 'Error': str(e)})
        
        # Вариант 2: Загрузка файла
        elif request.FILES.get('file'):
            file_obj = request.FILES['file']
            file_name = file_obj.name.lower()
            
            try:
                if file_name.endswith(('.yaml', '.yml')):
                    data = ProductImportService.load_yaml_from_file(file_obj)
                elif file_name.endswith('.json'):
                    data = ProductImportService.load_json_from_file(file_obj)
                else:
                    return Response({
                        'Status': False,
                        'Error': 'Неподдерживаемый формат файла. Используйте YAML или JSON'
                    })
            except Exception as e:
                return Response({'Status': False, 'Error': str(e)})
        
        else:
            return Response({
                'Status': False,
                'Error': 'Не указаны все необходимые аргументы. Укажите url или загрузите файл'
            })
        
        # Обработка импортированных данных
        result = ProductImportService.process_import_data(data, shop_id, request.user.id)
        
        if result.get('success'):
            return Response({
                'Status': True,
                'Message': result.get('message'),
                'Shop': result.get('shop_name'),
                'Categories': result.get('categories_count'),
                'Goods': result.get('goods_count')
            })
        else:
            return Response({
                'Status': False,
                'Error': result.get('error')
            })


class PartnerState(APIView):
    "API для управления статусом магазина (включен/выключен прием заказов)"
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        "Получить текущий статус магазина"
        if request.user.type != 'shop':
            return Response({'Status': False, 'Error': 'Только для магазинов'})
        
        try:
            shop = Shop.objects.get(user=request.user)
            return Response({
                'Status': True,
                'state': shop.state,
                'shop_name': shop.name
            })
        except Shop.DoesNotExist:
            return Response({'Status': False, 'Error': 'Магазин не найден'})
    
    def post(self, request):
        "Изменить статус магазина"
        if request.user.type != 'shop':
            return Response({'Status': False, 'Error': 'Только для магазинов'})
        
        state = request.data.get('state')
        if state is None:
            return Response({'Status': False, 'Error': 'Не указан параметр state'})
        
        try:
            shop = Shop.objects.get(user=request.user)
            shop.state = bool(state)
            shop.save()
            
            state_text = "включен" if shop.state else "выключен"
            return Response({
                'Status': True,
                'Message': f'Прием заказов {state_text}',
                'state': shop.state
            })
        except Shop.DoesNotExist:
            return Response({'Status': False, 'Error': 'Магазин не найден'})


class PartnerOrders(APIView):
    "  API для получения списка заказов магазина"
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        "Получить заказы, содержащие товары этого магазина"
        if request.user.type != 'shop':
            return Response({'Status': False, 'Error': 'Только для магазинов'})
        
        try:
            shop = Shop.objects.get(user=request.user)
            
            # Получаем все заказы, содержащие товары этого магазина
            from orders.models import Order, OrderItem
            
            orders = Order.objects.filter(
                ordered_items__product_info__shop=shop,
                state__in=['confirmed', 'assembled', 'sent', 'delivered'] 
            ).distinct()
            
            orders_data = []
            for order in orders:
                # Получаем только товары этого магазина в заказе
                items = OrderItem.objects.filter(
                    order=order,
                    product_info__shop=shop
                ).select_related('product_info__product')
                
                items_data = []
                for item in items:
                    items_data.append({
                        'id': item.id,
                        'product': item.product_info.product.name,
                        'model': item.product_info.model,
                        'quantity': item.quantity,
                        'price': item.product_info.price,
                        'total': item.quantity * item.product_info.price
                    })
                
                orders_data.append({
                    'order_id': order.id,
                    'created_at': order.dt,
                    'status': order.state,
                    'contact': {
                        'city': order.contact.city if order.contact else None,
                        'street': order.contact.street if order.contact else None,
                        'house': order.contact.house if order.contact else None,
                        'phone': order.contact.phone if order.contact else None
                    } if order.contact else None,
                    'items': items_data,
                    'items_count': len(items_data),
                    'total_amount': sum(item['total'] for item in items_data)
                })
            
            return Response({
                'Status': True,
                'Orders': orders_data,
                'Total': len(orders_data)
            })
            
        except Shop.DoesNotExist:
            return Response({'Status': False, 'Error': 'Магазин не найден'})