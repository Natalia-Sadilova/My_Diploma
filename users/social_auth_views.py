from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.contrib.auth import login
from social_django.utils import load_backend, load_strategy
from social_core.backends.oauth import BaseOAuth2
from rest_framework_simplejwt.tokens import RefreshToken
import logging

logger = logging.getLogger(__name__)


class SocialAuthUrlsView(APIView):
    """
    Возвращает URL для редиректа на авторизацию в соцсетях
    
    GET /api/v1/users/social/urls/
    Response: {
        "google": "http://localhost:8000/api/v1/auth/login/google/",
        "github": "http://localhost:8000/api/v1/auth/login/github/"
    }
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        base_url = request.build_absolute_uri('/api/v1/auth/')
        urls = {
            'google': f"{base_url}login/google/",
            'github': f"{base_url}login/github/",
        }
        return Response(urls)


class SocialAuthCompleteView(APIView):
    """
    Завершает OAuth авторизацию и возвращает JWT токен
    
    GET /api/v1/users/social/complete/google/?code=...&state=...
    """
    permission_classes = [AllowAny]
    
    def get(self, request, backend):
        try:
            # Загружаем стратегию и бэкенд
            strategy = load_strategy(request)
            backend_obj = load_backend(strategy, backend, redirect_uri=request.build_absolute_uri())
            
            # Завершаем аутентификацию
            user = backend_obj.complete(request.GET)
            
            if user and user.is_authenticated:
                # Логиним пользователя
                login(request, user)
                
                # Создаем JWT токены
                refresh = RefreshToken.for_user(user)
                
                return Response({
                    'Status': True,
                    'AccessToken': str(refresh.access_token),
                    'RefreshToken': str(refresh),
                    'User': {
                        'id': user.id,
                        'email': user.email,
                        'username': user.username,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                    }
                })
            else:
                return Response({
                    'Status': False,
                    'Error': 'Authentication failed'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Social auth error: {e}")
            return Response({
                'Status': False,
                'Error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)