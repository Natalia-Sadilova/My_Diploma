from django.urls import path
from . import views
from .social_auth_views import SocialAuthUrlsView, SocialAuthCompleteView

urlpatterns = [
    # Регистрация и авторизация
    path('register/', views.RegisterView.as_view(), name='register'),
    path('verify-email/', views.VerifyEmailView.as_view(), name='verify-email'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    
    # Профиль пользователя
    path('profile/', views.UserProfileView.as_view(), name='profile'),

    # Социальная авторизация
    path('social/urls/', SocialAuthUrlsView.as_view(), name='social-auth-urls'),
    path('social/complete/<str:backend>/', SocialAuthCompleteView.as_view(), name='social-auth-complete'),
]