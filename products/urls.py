from django.urls import path
from . import views

urlpatterns = [
    # API для поставщиков (магазинов)
    path('partner/update/', views.PartnerUpdate.as_view(), name='partner-update'),
    path('partner/state/', views.PartnerState.as_view(), name='partner-state'),
    path('partner/orders/', views.PartnerOrders.as_view(), name='partner-orders'),
    
    # Публичные API для товаров (для покупателей)
    path('', views.ProductListView.as_view(), name='product-list'),           # GET /api/v1/products/
    path('<int:pk>/', views.ProductDetailView.as_view(), name='product-detail'),  # GET /api/v1/products/1/
    path('categories/', views.CategoryListView.as_view(), name='category-list'),   # GET /api/v1/products/categories/
]