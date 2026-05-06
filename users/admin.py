from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, ConfirmEmailToken


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'username', 'type', 'company', 'is_active', 'is_verified')
    list_filter = ('type', 'is_active', 'is_verified')
    search_fields = ('email', 'username', 'company')
    fieldsets = UserAdmin.fieldsets + (
        ('Дополнительная информация', {'fields': ('type', 'company', 'position', 'is_verified')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Дополнительная информация', {'fields': ('type', 'company', 'position', 'email')}),
    )


@admin.register(ConfirmEmailToken)
class ConfirmEmailTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'key')
    readonly_fields = ('key', 'created_at')