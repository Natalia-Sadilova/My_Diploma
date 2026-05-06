from celery import shared_task
from django.core.files.base import ContentFile
from django.db import transaction
from django.conf import settings
import yaml
import json
import logging
import requests  # ← добавьте этот импорт
from shops.models import Shop
from .models import Category, Product, ProductInfo, Parameter, ProductParameter
from .services import ProductImportService
from django.core.files.storage import default_storage
from io import BytesIO
from PIL import Image

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=settings.IMPORT_MAX_RETRIES, default_retry_delay=settings.IMPORT_RETRY_DELAY)
def do_import(self, file_content, filename, shop_id, user_id):
    """Асинхронный импорт товаров из файла"""
    try:
        if filename.endswith(('.yaml', '.yml')):
            data = yaml.safe_load(file_content)
        elif filename.endswith('.json'):
            data = json.loads(file_content)
        else:
            raise ValueError(f"Неподдерживаемый формат файла: {filename}")
        
        result = ProductImportService.process_import_data(data, shop_id, user_id)
        
        if result.get('success'):
            logger.info(f"Import completed: {result['goods_count']} goods imported to shop {shop_id}")
            return result
        else:
            raise Exception(result.get('error'))
            
    except Exception as exc:
        logger.error(f"Import failed for shop {shop_id}: {exc}")
        raise self.retry(exc=exc, countdown=300)


@shared_task
def import_from_url(url, shop_id, user_id):
    """Асинхронный импорт товаров из URL"""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
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
def generate_product_thumbnails(product_id):
    """Асинхронная генерация миниатюр для товара"""
    from .models import Product
    
    try:
        product = Product.objects.get(id=product_id)
        if product.image:
            _ = product.thumbnail
            _ = product.small_thumbnail
            logger.info(f"Thumbnails generated for product {product_id}")
            return {'status': 'success', 'product_id': product_id}
        else:
            logger.warning(f"Product {product_id} has no image")
            return {'status': 'skipped', 'product_id': product_id, 'reason': 'no image'}
    except Product.DoesNotExist:
        logger.error(f"Product {product_id} not found")
        return {'status': 'error', 'error': 'Product not found'}


@shared_task
def generate_user_avatar_thumbnail(user_id):
    """Асинхронная генерация миниатюры аватара пользователя"""
    from users.models import User
    
    try:
        user = User.objects.get(id=user_id)
        if user.avatar:
            _ = user.avatar_thumbnail
            logger.info(f"Avatar thumbnail generated for user {user_id}")
            return {'status': 'success', 'user_id': user_id}
        else:
            logger.warning(f"User {user_id} has no avatar")
            return {'status': 'skipped', 'user_id': user_id, 'reason': 'no avatar'}
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found")
        return {'status': 'error', 'error': 'User not found'}


@shared_task
def batch_generate_all_thumbnails():
    """Периодическая задача для генерации всех миниатюр"""
    from .models import Product
    from users.models import User
    
    results = []
    
    products = Product.objects.filter(image__isnull=False)
    logger.info(f"Found {products.count()} products with images")
    
    for product in products:
        result = generate_product_thumbnails.delay(product.id)
        results.append({'product_id': product.id, 'task_id': result.id})
    
    users = User.objects.filter(avatar__isnull=False)
    logger.info(f"Found {users.count()} users with avatars")
    
    for user in users:
        result = generate_user_avatar_thumbnail.delay(user.id)
        results.append({'user_id': user.id, 'task_id': result.id})
    
    logger.info(f"Batch generation started for {len(results)} items")
    return {'status': 'started', 'total_tasks': len(results), 'tasks': results}