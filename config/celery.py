import os
from celery import Celery
from celery.schedules import crontab

# Устанавливаем переменную окружения для настроек Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Создаем экземпляр Celery
app = Celery('procurement')

# Загружаем настройки из Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматически находим задачи в приложениях
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    """Отладочная задача для проверки работы Celery"""
    print(f'Request: {self.request!r}')


# Планировщик задач 
app.conf.beat_schedule = {
    # Очистка старых токенов каждую ночь
    'cleanup-old-tokens': {
        'task': 'users.tasks.cleanup_expired_tokens',
        'schedule': crontab(hour=2, minute=0),
    },
    # Проверка неотправленных писем каждые 5 минут
    'retry-failed-emails': {
        'task': 'orders.tasks.retry_failed_order_notifications',
        'schedule': crontab(minute='*/5'),
    },
}

app.conf.timezone = 'Europe/Moscow'