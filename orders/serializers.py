# orders/serializers.py
from rest_framework import serializers
from .models import Contact, Order, OrderItem


class ContactSerializer(serializers.ModelSerializer):
    """Сериализатор для контактов"""
    class Meta:
        model = Contact
        fields = ['id', 'city', 'street', 'house', 'structure', 'building', 'apartment', 'phone']
        read_only_fields = ['id']


class OrderItemSerializer(serializers.ModelSerializer):
    """Сериализатор для позиций заказа"""
    product_name = serializers.CharField(source='product_info.product.name', read_only=True)
    shop_name = serializers.CharField(source='product_info.shop.name', read_only=True)
    price = serializers.DecimalField(source='product_info.price', max_digits=10, decimal_places=2, read_only=True)
    subtotal = serializers.SerializerMethodField()
    
    class Meta:
        model = OrderItem
        fields = ['id', 'product_name', 'shop_name', 'quantity', 'price', 'subtotal']
    
    def get_subtotal(self, obj):
        return obj.quantity * obj.product_info.price


class OrderSerializer(serializers.ModelSerializer):
    """Сериализатор для списка заказов"""
    total_amount = serializers.SerializerMethodField()
    items_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = ['id', 'dt', 'state', 'total_amount', 'items_count']
    
    def get_total_amount(self, obj):
        return sum(item.quantity * item.product_info.price for item in obj.ordered_items.all())
    
    def get_items_count(self, obj):
        return obj.ordered_items.count()


class OrderDetailSerializer(serializers.ModelSerializer):
    """Сериализатор для детальной информации о заказе"""
    items = OrderItemSerializer(source='ordered_items', many=True, read_only=True)
    contact = ContactSerializer(read_only=True)
    total_amount = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = ['id', 'dt', 'state', 'contact', 'items', 'total_amount']
    
    def get_total_amount(self, obj):
        return sum(item.quantity * item.product_info.price for item in obj.ordered_items.all())