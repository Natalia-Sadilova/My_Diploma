from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import generics, filters
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from django_filters.rest_framework import DjangoFilterBackend
import yaml
import json

from .services import ProductImportService
from .tasks import do_import  # Импорт Celery задачи
from shops.models import Shop
from .models import Category, Product, ProductInfo
from .serializers import CategorySerializer, ProductSerializer, ProductInfoSerializer


class PartnerUpdate(APIView):
    """
    API для обновления прайса от поставщика (магазина)
    
    Поддерживает:
    - Загрузку файла (YAML или JSON) - асинхронно через Celery
    - Импорт по URL - синхронно
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
        
        # Вариант 1: Импорт по URL (синхронно)
        url = request.data.get('url')
        if url:
            try:
                validator = URLValidator()
                validator(url)
                data = ProductImportService.load_yaml_from_url(url)
                
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
            except ValidationError as e:
                return Response({'Status': False, 'Error': f'Некорректный URL: {str(e)}'})
            except Exception as e:
                return Response({'Status': False, 'Error': str(e)})
        
        # Вариант 2: Загрузка файла (АСИНХРОННО через Celery)
        elif request.FILES.get('file'):
            file_obj = request.FILES['file']
            file_name = file_obj.name.lower()
            
            # Проверка формата файла
            if not (file_name.endswith(('.yaml', '.yml', '.json'))):
                return Response({
                    'Status': False,
                    'Error': 'Неподдерживаемый формат файла. Используйте YAML или JSON'
                })
            
            # Запускаем асинхронный импорт через Celery
            file_content = file_obj.read()
            task = do_import.delay(
                file_content=file_content,
                filename=file_name,
                shop_id=shop_id,
                user_id=request.user.id
            )
            
            return Response({
                'Status': True,
                'Message': 'Импорт запущен в фоновом режиме',
                'TaskId': task.id
            }, status=status.HTTP_202_ACCEPTED)
        
        else:
            return Response({
                'Status': False,
                'Error': 'Не указаны все необходимые аргументы. Укажите url или загрузите файл'
            }, status=status.HTTP_400_BAD_REQUEST)


class PartnerState(APIView):
    """API для управления статусом магазина (включен/выключен прием заказов)"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Получить текущий статус магазина"""
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
        """Изменить статус магазина"""
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
    """API для получения списка заказов магазина"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Получить заказы, содержащие товары этого магазина"""
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


class CategoryListView(generics.ListAPIView):
    """
    Список всех категорий
    
    GET /api/v1/products/categories/
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]


class ProductListView(generics.ListAPIView):
    """
    Список товаров с фильтрацией
    
    GET /api/v1/products/
    
    Параметры фильтрации:
    - category_id: ID категории
    - shop_id: ID магазина
    - min_price: минимальная цена
    - max_price: максимальная цена
    - search: поиск по названию
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category_id']
    search_fields = ['name', 'category__name']
    ordering_fields = ['name']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Фильтр по магазину
        shop_id = self.request.query_params.get('shop_id')
        if shop_id:
            queryset = queryset.filter(product_infos__shop_id=shop_id)
        
        # Фильтр по цене
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        
        if min_price:
            queryset = queryset.filter(product_infos__price__gte=min_price)
        if max_price:
            queryset = queryset.filter(product_infos__price__lte=max_price)
        
        return queryset.distinct()


class ProductDetailView(generics.RetrieveAPIView):
    """
    Детальная информация о товаре
    
    GET /api/v1/products/<id>/
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data
        
        # Добавляем информацию о наличии от разных магазинов
        product_infos = ProductInfo.objects.filter(
            product=instance,
            shop__state=True,  # Только активные магазины
            quantity__gt=0     # Только товары в наличии
        ).select_related('shop')
        
        data['product_infos'] = ProductInfoSerializer(product_infos, many=True).data
        
        return Response(data)