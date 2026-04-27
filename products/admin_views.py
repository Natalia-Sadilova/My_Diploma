from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from .tasks import do_import, import_from_url
from shops.models import Shop


@staff_member_required
def admin_import_products(request):
    """
    Админский view для запуска импорта товаров
    Доступен только для персонала
    """
    if request.method == 'POST':
        shop_id = request.POST.get('shop_id')
        import_type = request.POST.get('import_type')  # 'file' or 'url'
        
        if not shop_id:
            messages.error(request, 'Выберите магазин')
            return redirect('admin:import_products')
        
        try:
            shop = Shop.objects.get(id=shop_id)
        except Shop.DoesNotExist:
            messages.error(request, 'Магазин не найден')
            return redirect('admin:import_products')
        
        if import_type == 'file' and request.FILES.get('import_file'):
            file_obj = request.FILES['import_file']
            file_content = file_obj.read()
            filename = file_obj.name
            
            task = do_import.delay(
                file_content=file_content,
                filename=filename,
                shop_id=shop_id,
                user_id=shop.user.id if shop.user else None
            )
            
            messages.success(
                request, 
                f'Импорт для магазина "{shop.name}" запущен. ID задачи: {task.id}'
            )
            
        elif import_type == 'url' and request.POST.get('import_url'):
            url = request.POST['import_url']
            
            task = import_from_url.delay(
                url=url,
                shop_id=shop_id,
                user_id=shop.user.id if shop.user else None
            )
            
            messages.success(
                request, 
                f'Импорт по URL для магазина "{shop.name}" запущен. ID задачи: {task.id}'
            )
            
        else:
            messages.error(request, 'Не указан файл или URL для импорта')
        
        return redirect('admin:import_products')
    
    # GET запрос - показываем форму
    shops = Shop.objects.all()
    
    context = {
        'shops': shops,
        'title': 'Импорт товаров'
    }
    
    return render(request, 'admin/products/import_products.html', context)


@staff_member_required
def admin_import_status(request, task_id):
    """
    Проверка статуса задачи импорта
    """
    from celery.result import AsyncResult
    
    task = AsyncResult(task_id)
    
    if task.ready():
        if task.successful():
            result = task.result
            return JsonResponse({
                'status': 'completed',
                'result': result
            })
        else:
            return JsonResponse({
                'status': 'failed',
                'error': str(task.info)
            })
    else:
        return JsonResponse({
            'status': 'pending',
            'task_id': task_id
        })