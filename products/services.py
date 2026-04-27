import yaml
import json
from urllib.request import urlopen
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from shops.models import Shop
from .models import Category, Product, ProductInfo, Parameter, ProductParameter


class ProductImportService:
    """Сервис для импорта товаров из YAML/JSON файлов"""
    
    @staticmethod
    def load_yaml_from_url(url):
        """Загрузка YAML данных из URL"""
        validator = URLValidator()
        try:
            validator(url)
        except ValidationError as e:
            raise ValueError(f"Некорректный URL: {e}")
        
        try:
            response = urlopen(url)
            data = yaml.safe_load(response.read())
            return data
        except Exception as e:
            raise ValueError(f"Ошибка загрузки данных: {e}")
    
    @staticmethod
    def load_yaml_from_file(file_obj):
        """Загрузка YAML данных из файла"""
        try:
            data = yaml.safe_load(file_obj.read())
            return data
        except Exception as e:
            raise ValueError(f"Ошибка чтения YAML файла: {e}")
    
    @staticmethod
    def load_json_from_file(file_obj):
        """Загрузка JSON данных из файла"""
        try:
            data = json.load(file_obj)
            return data
        except Exception as e:
            raise ValueError(f"Ошибка чтения JSON файла: {e}")
    
    @staticmethod
    def process_import_data(data, shop_id, user_id):
        """
        Обработка данных импорта и сохранение в БД
        
        Ожидаемая структура data:
        {
            'shop': 'Название магазина',
            'categories': [
                {'id': 1, 'name': 'Категория 1'},
                ...
            ],
            'goods': [
                {
                    'id': 123,
                    'category': 1,
                    'model': 'Модель',
                    'name': 'Название товара',
                    'price': 1000,
                    'price_rrc': 1200,
                    'quantity': 10,
                    'parameters': {
                        'Диагональ': '15 дюймов',
                        'Процессор': 'Intel i5'
                    }
                },
                ...
            ]
        }
        """
        try:
            # Получаем или создаем магазин (поставщика)
            shop_name = data.get('shop')
            if not shop_name:
                raise ValueError("Не указано название магазина в файле")
            
            shop, created = Shop.objects.get_or_create(
                name=shop_name,
                defaults={'user_id': user_id}
            )
            
            # Обрабатываем категории
            for category_data in data.get('categories', []):
                category_id = category_data.get('id')
                category_name = category_data.get('name')
                
                if not category_id or not category_name:
                    continue
                
                category, _ = Category.objects.get_or_create(
                    id=category_id,
                    defaults={'name': category_name}
                )
                # Если имя изменилось, обновляем
                if category.name != category_name:
                    category.name = category_name
                    category.save()
                
                # Добавляем магазин в категорию (связь многие-ко-многим)
                category.shops.add(shop)
            
            # Удаляем старую информацию о товарах этого магазина
            ProductInfo.objects.filter(shop_id=shop.id).delete()
            
            # Обрабатываем товары
            goods_count = 0
            for item in data.get('goods', []):
                try:
                    category_id = item.get('category')
                    product_name = item.get('name')
                    
                    if not category_id or not product_name:
                        continue
                    
                    # Получаем или создаем товар
                    product, _ = Product.objects.get_or_create(
                        name=product_name,
                        category_id=category_id
                    )
                    
                    # Создаем информацию о товаре для этого магазина
                    product_info = ProductInfo.objects.create(
                        product=product,
                        shop=shop,
                        external_id=item.get('id', 0),
                        model=item.get('model', ''),
                        price=item.get('price', 0),
                        price_rrc=item.get('price_rrc', 0),
                        quantity=item.get('quantity', 0)
                    )
                    
                    # Обрабатываем параметры товара
                    for param_name, param_value in item.get('parameters', {}).items():
                        if not param_name:
                            continue
                        
                        parameter, _ = Parameter.objects.get_or_create(name=param_name)
                        ProductParameter.objects.create(
                            product_info=product_info,
                            parameter=parameter,
                            value=str(param_value)
                        )
                    
                    goods_count += 1
                    
                except IntegrityError as e:
                    print(f"Ошибка при импорте товара {product_name}: {e}")
                    continue
            
            return {
                'success': True,
                'shop_name': shop.name,
                'categories_count': len(data.get('categories', [])),
                'goods_count': goods_count,
                'message': f'Импортировано {goods_count} товаров'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }