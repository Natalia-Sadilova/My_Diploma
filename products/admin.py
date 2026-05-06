# products/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Product, ProductInfo, Parameter, ProductParameter

class ProductParameterInline(admin.TabularInline):
    model = ProductParameter
    extra = 1
    classes = ('collapse',)


class ProductInfoInline(admin.TabularInline):
    model = ProductInfo
    extra = 1
    classes = ('collapse',)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    # Убираем поля, которых нет в модели
    list_display = ('id', 'name', 'category', 'image_preview')
    list_filter = ('category',)
    search_fields = ('name',)
    readonly_fields = ('image_preview_large',)
    
    fieldsets = (
        (None, {
            'fields': ('name', 'category')
        }),
        ('Изображения', {
            'fields': ('image', 'image_preview_large')
        }),
    )
    
    def image_preview(self, obj):
        if obj.thumbnail:  # Используем thumbnail из ImageSpecField
            return format_html('<img src="{}" width="50" height="50" />', obj.thumbnail.url)
        elif obj.image:
            return format_html('<img src="{}" width="50" height="50" />', obj.image.url)
        return "-"
    image_preview.short_description = 'Миниатюра'
    
    def image_preview_large(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="200" />', obj.image.url)
        return "Нет изображения"
    image_preview_large.short_description = 'Просмотр'


@admin.register(ProductInfo)
class ProductInfoAdmin(admin.ModelAdmin):
    list_display = ('product', 'shop', 'price', 'quantity')
    list_filter = ('shop',)
    search_fields = ('product__name', 'model')
    inlines = [ProductParameterInline]


@admin.register(Parameter)
class ParameterAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)