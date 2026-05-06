# performance/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.conf import settings
from products.models import Product, Category, ProductInfo
from products.views import PartnerOrders
import time


class PerformanceTestView(APIView):
    """
    Тестирование производительности кэширования
    
    GET /api/v1/performance/test/
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        results = {
            'without_cache': {},
            'with_cache': {},
            'comparison': {}
        }
        
        # Тест 1: Получение всех товаров с фильтрацией
        start = time.time()
        products = list(Product.objects.select_related('category').all()[:100])
        results['without_cache']['products_query'] = round((time.time() - start) * 1000, 2)
        
        start = time.time()
        products_cached = list(Product.objects.cache().select_related('category').all()[:100])
        results['with_cache']['products_query'] = round((time.time() - start) * 1000, 2)
        
        # Тест 2: Получение информации о товарах
        start = time.time()
        product_infos = list(ProductInfo.objects.select_related('product', 'shop')[:50])
        results['without_cache']['product_infos_query'] = round((time.time() - start) * 1000, 2)
        
        start = time.time()
        product_infos_cached = list(ProductInfo.objects.cache().select_related('product', 'shop')[:50])
        results['with_cache']['product_infos_query'] = round((time.time() - start) * 1000, 2)
        
        # Сравнение
        for key in results['without_cache']:
            without = results['without_cache'][key]
            with_cache = results['with_cache'][key]
            if without > 0:
                speedup = round((without - with_cache) / without * 100, 1)
            else:
                speedup = 0
            results['comparison'][key] = {
                'without_cache_ms': without,
                'with_cache_ms': with_cache,
                'speedup_percent': speedup,
                'faster': f"{speedup}% быстрее" if speedup > 0 else "медленнее"
            }
        
        results['cache_info'] = {
            'redis_configured': bool(getattr(settings, 'CACHEOPS_REDIS', False)),
        }
        
        return Response(results)


class PartnerOrdersProfilerView(APIView):
    """
    Тестовый эндпоинт для профилирования PartnerOrders через Silk
    
    GET /api/v1/performance/profile/partner-orders/
    Требуется авторизация с токеном пользователя типа 'shop'
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Вызываем метод через Silk (будет автоматически профилирован)
        response = PartnerOrders().get(request)
        
        return Response({
            'status': 'success',
            'message': 'Request profiled. Check /silk/ for details',
            'data': response.data
        })
