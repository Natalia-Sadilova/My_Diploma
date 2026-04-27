# orders/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Контакты
    path('contacts/', views.ContactListCreateView.as_view(), name='contact-list'),
    path('contacts/<int:pk>/', views.ContactDetailView.as_view(), name='contact-detail'),
    
    # Заказы
    path('', views.OrderListView.as_view(), name='order-list'),
    path('<int:pk>/', views.OrderDetailView.as_view(), name='order-detail'),
    path('confirm/', views.ConfirmOrderView.as_view(), name='order-confirm'),
]