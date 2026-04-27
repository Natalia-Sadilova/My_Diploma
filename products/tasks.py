from celery import shared_task
from django.core.files.base import ContentFile
from django.db import transaction
from django.conf import settings  # <-- ВАЖНО: импорт settings
import yaml
import json
import logging
from shops.models import Shop
from .models import Category, Product, ProductInfo, Parameter, ProductParameter
from .services import ProductImportService

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=settings.IMPORT_MAX_RETRIES, default_retry_delay=settings.IMPORT_RETRY_DELAY)
def do_import(self, file_content, filename, shop_id, user_id):
    """
    Асинхронный импорт товаров из файла
    
    Args:
        file_content: Содержимое файла (бинарные данные)
        filename: Имя файла
        shop_id: ID магазина
        user_id: ID пользователя
    """
    try:
        # Определяем формат файла
        if filename.endswith(('.yaml', '.yml')):
            data = yaml.safe_load(file_content)
        elif filename.endswith('.json'):
            data = json.loads(file_content)
        else:
            raise ValueError(f"Неподдерживаемый формат файла: {filename}")
        
        # Импортируем данные
        result = ProductImportService.process_import_data(data, shop_id, user_id)
        
        if result.get('success'):
            logger.info(f"Import completed: {result['goods_count']} goods imported to shop {shop_id}")
            return result
        else:
            raise Exception(result.get('error'))
            
    except Exception as exc:
        logger.error(f"Import failed for shop {shop_id}: {exc}")
        raise self.retry(exc=exc, countdown=300)  # Повтор через 5 минут


@shared_task
def import_from_url(url, shop_id, user_id):
    """
    Асинхронный импорт товаров из URL
    
    Args:
        url: URL для загрузки
        shop_id: ID магазина
        user_id: ID пользователя
    """
    import requests
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Определяем формат по URL
        if url.endswith(('.yaml', '.yml')):
            data = yaml.safe_load(response.content)
        elif url.endswith('.json'):
            data = response.json()
        else:
            raise ValueError(f"Неподдерживаемый формат: {url}")
        
        result = ProductImportService.process_import_data(data, shop_id, user_id)
        
        if result.get('success'):
            logger.info(f"Import from URL completed: {result['goods_count']} goods")
            return result
        else:
            raise Exception(result.get('error'))
            
    except Exception as exc:
        logger.error(f"Import from URL failed: {exc}")
        return {'success': False, 'error': str(exc)}


@shared_task
def update_all_shops_prices():
    """
    Периодическая задача для обновления цен у всех магазинов
    (например, по расписанию)
    """
    from shops.models import Shop
    
    shops = Shop.objects.filter(state=True)
    results = []
    
    for shop in shops:
        if shop.url:
            try:
                result = import_from_url.delay(shop.url, shop.id, shop.user.id)
                results.append({
                    'shop_id': shop.id,
                    'shop_name': shop.name,
                    'task_id': result.id
                })
            except Exception as e:
                logger.error(f"Failed to start import for shop {shop.name}: {e}")
                results.append({
                    'shop_id': shop.id,
                    'shop_name': shop.name,
                    'error': str(e)
                })
    
    return results