from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, ConfirmEmailToken


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'username', 'type', 'company', 'is_active')
    list_filter = ('type', 'is_active')
    search_fields = ('email', 'username', 'company')
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('type', 'company', 'position')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Info', {'fields': ('type', 'company', 'position', 'email')}),
    )


@admin.register(ConfirmEmailToken)
class ConfirmEmailTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'key')