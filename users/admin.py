from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, ConfirmEmailToken
from django.utils.html import format_html

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'username', 'type', 'company', 'is_active', 'is_verified', 'avatar_preview')
    list_filter = ('type', 'is_active', 'is_verified')
    search_fields = ('email', 'username', 'company')
    
    fieldsets = UserAdmin.fieldsets + (
        ('Дополнительная информация', {'fields': ('type', 'company', 'position', 'is_verified')}),
        ('Аватар', {'fields': ('avatar', 'avatar_thumbnail')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Дополнительная информация', {'fields': ('type', 'company', 'position', 'email')}),
    )
    
    def avatar_preview(self, obj):
        if obj.avatar_thumbnail:
            return format_html('<img src="{}" width="32" height="32" style="border-radius: 50%;" />', obj.avatar_thumbnail.url)
        return "-"
    avatar_preview.short_description = 'Аватар'


@admin.register(ConfirmEmailToken)
class ConfirmEmailTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'key')
    readonly_fields = ('key', 'created_at')