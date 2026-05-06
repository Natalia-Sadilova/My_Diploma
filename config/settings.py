import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-your-secret-key-here')
DEBUG = os.getenv('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

INSTALLED_APPS = [
    'baton',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    'rest_framework',
    'rest_framework_simplejwt',
    'django_rest_passwordreset',
    'corsheaders',
    'debug_toolbar',
    'django_filters',
    'drf_spectacular',
    'social_django',
    'imagekit',
    
    'users',
    'products',
    'orders',
    'shops',
    'cart',

    'baton.autodiscover',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = 'media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom user model
AUTH_USER_MODEL = 'users.User'

# REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',

    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle', # Для неавторизованных пользователей
        'rest_framework.throttling.UserRateThrottle', # Для авторизованных пользователей
    ],

    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/day',           # Аноним: 100 запросов в день
        'user': '1000/day',          # Пользователь: 1000 запросов в день
        'registration': '3/hour',    # Регистрация: 3 попытки в час
    }
}

# JWT Settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}

# CORS settings
CORS_ALLOWED_ORIGINS = os.getenv('CORS_ALLOWED_ORIGINS', 'http://localhost:3000').split(',')
CORS_ALLOW_CREDENTIALS = True

# Email settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER)

# Celery settings
CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')
CELERY_RESULT_BACKEND = os.getenv('REDIS_URL', 'redis://localhost:6379')
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

# Celery Configuration
CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Europe/Moscow'
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 минут

# Celery Beat (периодические задачи)
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# Настройки для email задач
EMAIL_MAX_RETRIES = 3
EMAIL_RETRY_DELAY = 60  # секунд

# Настройки для импорта
IMPORT_MAX_RETRIES = 2
IMPORT_RETRY_DELAY = 300  # 5 минут

SPECTACULAR_SETTINGS = {
    'TITLE': 'Procurement API',
    'DESCRIPTION': 'API для системы закупок',
    'VERSION': '1.0.0',
}

# Авторизация через соцсети 

AUTHENTICATION_BACKENDS = (
    'social_core.backends.google.GoogleOAuth2',   # Google авторизация
    'social_core.backends.github.GithubOAuth2',   # GitHub авторизация
    'django.contrib.auth.backends.ModelBackend',  # Стандартный вход по email/паролю
)

# Настройки для Google OAuth2
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = os.getenv('SOCIAL_AUTH_GOOGLE_OAUTH2_KEY', '')
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = os.getenv('SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET', '')

# Настройки для GitHub OAuth2
SOCIAL_AUTH_GITHUB_KEY = os.getenv('SOCIAL_AUTH_GITHUB_KEY', '')
SOCIAL_AUTH_GITHUB_SECRET = os.getenv('SOCIAL_AUTH_GITHUB_SECRET', '')

# Запрашиваем email и профиль)
SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE = [
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
]

SOCIAL_AUTH_GITHUB_SCOPE = ['user:email']

SOCIAL_AUTH_USER_FIELDS = ['email', 'username', 'first_name', 'last_name']

LOGIN_REDIRECT_URL = '/api/v1/users/profile/'
LOGIN_URL = '/api/v1/users/login/'

SOCIAL_AUTH_CREATE_USERS = True

SOCIAL_AUTH_UPDATE_DETAILS_FROM_SOCIAL = True

SOCIAL_AUTH_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.auth_allowed',
    'social_core.pipeline.social_auth.social_user',
    'social_core.pipeline.user.get_username',
    'social_core.pipeline.user.create_user',
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details',
)

# Настройка вида админки
BATON = {
    'SITE_HEADER': 'Procurement Admin',
    'SITE_TITLE': 'Администрирование',
    'INDEX_TITLE': 'Панель управления закупками',
    'SUPPORT_HREF': 'https://github.com/otto-torino/django-baton/issues',
    'COPYRIGHT': '© 2025 Procurement System',
    'POWERED_BY': '<a href="https://github.com/otto-torino/django-baton">Django Baton</a>',
    'CONFIRM_UNSAVED_CHANGES': True,
    'SHOW_MULTIPART_UPLOADING': True,
    'ENABLE_IMAGES_PREVIEW': True,
    'CHANGEFORM_FIXED_SUBMIT_ROW': True,
    'MENU_TITLE': 'Меню',
    'MENU_ALWAYS_COLLAPSED': False,
    'MESSAGES_TOASTS': ['warning', 'error'],
    'GRAVATAR_ENABLED': False,
    'FORCE_THEME': None,  # 'light' или 'dark'
    
    # Настройка меню
    'MENU': (
        { 'type': 'title', 'label': 'Управление', 'icon': 'dashboard' },
        
        { 'type': 'app', 'name': 'users', 'label': 'Пользователи', 'icon': 'people' },
        { 'type': 'app', 'name': 'shops', 'label': 'Магазины', 'icon': 'store' },
        { 'type': 'app', 'name': 'products', 'label': 'Товары', 'icon': 'inventory' },
        { 'type': 'app', 'name': 'orders', 'label': 'Заказы', 'icon': 'shopping_cart' },
        
        { 'type': 'title', 'label': 'Дополнительно', 'icon': 'settings' },
        { 'type': 'model', 'label': 'Импорт товаров', 'name': 'import', 'app': 'products', 'icon': 'upload_file' },
    ),
}