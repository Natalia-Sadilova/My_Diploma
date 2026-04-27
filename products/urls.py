from django.urls import path
from . import views

urlpatterns = [
    # API для поставщиков (магазинов)
    path('partner/update/', views.PartnerUpdate.as_view(), name='partner-update'),
    path('partner/state/', views.PartnerState.as_view(), name='partner-state'),
    path('partner/orders/', views.PartnerOrders.as_view(), name='partner-orders'),
    
]