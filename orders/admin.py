from django.contrib import admin
from .models import Contact, Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    readonly_fields = ('product_info', 'quantity')
    can_delete = False
    classes = ('collapse',)


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('user', 'city', 'street', 'house', 'phone')
    list_filter = ('city',)
    search_fields = ('user__email', 'city', 'street', 'phone')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'dt', 'state', 'contact')
    list_filter = ('state', 'dt')
    search_fields = ('user__email',)
    inlines = [OrderItemInline]
    readonly_fields = ('dt',)
    
    actions = ['mark_as_confirmed', 'mark_as_delivered']
    
    def mark_as_confirmed(self, request, queryset):
        queryset.update(state='confirmed')
    mark_as_confirmed.short_description = 'Отметить как подтверждённые'
    
    def mark_as_delivered(self, request, queryset):
        queryset.update(state='delivered')
    mark_as_delivered.short_description = 'Отметить как доставленные'