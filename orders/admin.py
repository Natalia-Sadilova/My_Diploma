from django.contrib import admin
from .models import Contact, Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('user', 'city', 'street', 'phone')
    list_filter = ('city',)
    search_fields = ('user__email', 'city', 'street')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'dt', 'state', 'contact')
    list_filter = ('state', 'dt')
    search_fields = ('user__email',)
    inlines = [OrderItemInline]
    readonly_fields = ('dt',)