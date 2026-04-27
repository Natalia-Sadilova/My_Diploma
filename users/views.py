from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction

from .models import User, ConfirmEmailToken
from .serializers import (
    UserSerializer, 
    RegisterSerializer, 
    LoginSerializer, 
    UserUpdateSerializer
)


class RegisterView(generics.CreateAPIView):
    """
    Регистрация нового пользователя
    
    POST /api/v1/users/register/
    {
        "email": "user@example.com",
        "username": "username",
        "password": "strongpass123",
        "password2": "strongpass123",
        "first_name": "Иван",
        "last_name": "Иванов",
        "type": "buyer"  # или "shop"
    }
    """
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        with transaction.atomic():
            user = serializer.save()
            
            # Создаем токен подтверждения
            token = ConfirmEmailToken.objects.create(user=user)
            
            # Отправляем email с подтверждением
            verification_url = f"{settings.BASE_URL}/api/v1/users/verify-email/?token={token.key}"
            
            try:
                send_mail(
                    subject='Подтверждение регистрации',
                    message=f'Здравствуйте! Для подтверждения регистрации перейдите по ссылке:\n{verification_url}',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
            except Exception as e:
                print(f"Email send error: {e}")
        
        return Response({
            'Status': True,
            'Message': 'Регистрация успешна. На вашу почту отправлено письмо с подтверждением.',
            'User': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        with transaction.atomic():
            user = serializer.save()
            token = ConfirmEmailToken.objects.create(user=user)
            
            # Асинхронная отправка email
            send_verification_email.delay(
                user_id=user.id,
                user_email=user.email,
                verification_token=token.key
            )
        
        return Response({
            'Status': True,
            'Message': 'Регистрация успешна. На вашу почту отправлено письмо с подтверждением.'
        }, status=status.HTTP_201_CREATED)


class VerifyEmailView(APIView):
    """
    Подтверждение email по токену
    
    GET /api/v1/users/verify-email/?token=<token>
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        token_key = request.query_params.get('token')
        
        if not token_key:
            return Response({'Status': False, 'Error': 'Токен не указан'}, status=400)
        
        try:
            token = ConfirmEmailToken.objects.get(key=token_key)
            user = token.user
            user.is_active = True
            user.save()
            token.delete()
            
            return Response({
                'Status': True,
                'Message': 'Email успешно подтвержден. Теперь вы можете войти в систему.'
            })
        except ConfirmEmailToken.DoesNotExist:
            return Response({'Status': False, 'Error': 'Недействительный токен'}, status=400)


class LoginView(APIView):
    """
    Вход пользователя
    
    POST /api/v1/users/login/
    {
        "email": "user@example.com",
        "password": "strongpass123"
    }
    """
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        
        user = authenticate(email=email, password=password)
        
        if not user:
            return Response({
                'Status': False,
                'Error': 'Неверный email или пароль'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        if not user.is_active:
            return Response({
                'Status': False,
                'Error': 'Email не подтвержден. Проверьте вашу почту.'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'Status': True,
            'AccessToken': str(refresh.access_token),
            'RefreshToken': str(refresh),
            'User': UserSerializer(user).data
        })


class LogoutView(APIView):
    """
    Выход пользователя (черный список токена)
    
    POST /api/v1/users/logout/
    {
        "refresh": "refresh_token_string"
    }
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response({'Status': False, 'Error': 'Не указан refresh токен'}, status=400)
            
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            return Response({'Status': True, 'Message': 'Выход выполнен успешно'})
        except Exception as e:
            return Response({'Status': False, 'Error': str(e)}, status=400)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    Просмотр и редактирование профиля пользователя
    
    GET /api/v1/users/profile/
    PATCH /api/v1/users/profile/
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UserUpdateSerializer
    
    def get_object(self):
        return self.request.user