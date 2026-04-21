from django.contrib import admin
from .models import Order, OrderItem

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'total_amount', 'status', 'created_at']
    list_editable = ['status']
    list_filter = ['status', 'created_at']

admin.site.register(OrderItem)
