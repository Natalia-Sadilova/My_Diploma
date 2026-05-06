from django.contrib import admin
from .models import Category, Product, ProductInfo, Parameter, ProductParameter


class ProductInfoInline(admin.TabularInline):
    model = ProductInfo
    extra = 1
    classes = ('collapse',)



class ProductParameterInline(admin.TabularInline):
    model = ProductParameter
    extra = 1
    classes = ('collapse',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)} if hasattr(Category, 'slug') else {}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category')
    list_filter = ('category',)
    search_fields = ('name',)
    inlines = [ProductInfoInline]


@admin.register(ProductInfo)
class ProductInfoAdmin(admin.ModelAdmin):
    list_display = ('product', 'shop', 'external_id', 'price', 'quantity')
    list_filter = ('shop',)
    search_fields = ('product__name', 'model')
    inlines = [ProductParameterInline]


@admin.register(Parameter)
class ParameterAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)