from rest_framework import serializers
from .models import Category, Product, ProductInfo, Parameter, ProductParameter


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    image_url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    small_thumbnail_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'category', 'category_name',
            'image_url', 'thumbnail_url', 'small_thumbnail_url'
        ]
    
    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return None
    
    def get_thumbnail_url(self, obj):
        if obj.image:
            return obj.thumbnail.url
        return None
    
    def get_small_thumbnail_url(self, obj):
        if obj.image:
            return obj.small_thumbnail.url
        return None


class ParameterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parameter
        fields = ['id', 'name']


class ProductParameterSerializer(serializers.ModelSerializer):
    parameter_name = serializers.CharField(source='parameter.name', read_only=True)
    
    class Meta:
        model = ProductParameter
        fields = ['id', 'parameter', 'parameter_name', 'value']


class ProductInfoSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    shop_name = serializers.CharField(source='shop.name', read_only=True)
    parameters = ProductParameterSerializer(source='product_parameters', many=True, read_only=True)
    product_image = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductInfo
        fields = [
            'id', 'product', 'product_name', 'shop', 'shop_name',
            'external_id', 'model', 'price', 'price_rrc', 'quantity',
            'parameters', 'product_image'
        ]
    
    def get_product_image(self, obj):
        if obj.product.image:
            return obj.product.thumbnail.url
        return None