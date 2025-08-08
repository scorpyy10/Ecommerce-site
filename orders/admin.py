from django.contrib import admin
from .models import Order, OrderItem, PaymentLog, DownloadLog
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['project_title', 'project_price', 'delivered_at', 'created_at']
    fields = ['project', 'project_title', 'project_price', 'quantity', 'delivery_status', 'delivery_url', 'delivered_at']


class PaymentLogInline(admin.TabularInline):
    model = PaymentLog
    extra = 0
    readonly_fields = ['created_at']
    fields = ['razorpay_payment_id', 'razorpay_order_id', 'amount', 'status', 'method', 'created_at']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_id', 'user', 'customer_name', 'total_amount', 'status', 'payment_status', 'created_at']
    list_filter = ['status', 'payment_status', 'created_at']
    search_fields = ['order_id', 'user__username', 'customer_name', 'customer_email', 'razorpay_order_id']
    readonly_fields = ['order_id', 'created_at', 'updated_at', 'completed_at']
    inlines = [OrderItemInline, PaymentLogInline]
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_id', 'user', 'total_amount', 'status')
        }),
        ('Payment Details', {
            'fields': ('payment_status', 'razorpay_order_id', 'razorpay_payment_id', 'razorpay_signature')
        }),
        ('Customer Information', {
            'fields': ('customer_name', 'customer_email', 'customer_phone')
        }),
        ('Notes', {
            'fields': ('notes', 'admin_notes'),
            'classes': ['collapse']
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ['collapse']
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
    
    actions = ['mark_as_completed', 'mark_as_processing']
    
    def mark_as_completed(self, request, queryset):
        updated = queryset.update(status='completed')
        self.message_user(request, f'{updated} orders marked as completed.')
    mark_as_completed.short_description = "Mark selected orders as completed"
    
    def mark_as_processing(self, request, queryset):
        updated = queryset.update(status='processing')
        self.message_user(request, f'{updated} orders marked as processing.')
    mark_as_processing.short_description = "Mark selected orders as processing"


class DownloadLogInline(admin.TabularInline):
    model = DownloadLog
    extra = 0
    readonly_fields = ['user', 'ip_address', 'user_agent', 'downloaded_at']


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'project_title', 'quantity', 'project_price', 'delivery_status', 'download_count', 'delivered_at']
    list_filter = ['delivery_status', 'delivered_at', 'created_at']
    search_fields = ['project_title', 'order__order_id', 'order__user__username']
    readonly_fields = ['project_title', 'project_price', 'created_at', 'updated_at']
    inlines = [DownloadLogInline]
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order', 'project', 'project_title', 'project_price', 'quantity')
        }),
        ('Delivery', {
            'fields': ('delivery_status', 'delivery_url', 'delivery_file', 'delivered_at')
        }),
        ('Access Control', {
            'fields': ('download_count', 'max_downloads', 'access_expires_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ['collapse']
        })
    )
    
    actions = ['mark_as_delivered', 'reset_download_count']
    
    def mark_as_delivered(self, request, queryset):
        updated = queryset.update(delivery_status='delivered')
        self.message_user(request, f'{updated} items marked as delivered.')
    mark_as_delivered.short_description = "Mark selected items as delivered"
    
    def reset_download_count(self, request, queryset):
        updated = queryset.update(download_count=0)
        self.message_user(request, f'{updated} items download count reset.')
    reset_download_count.short_description = "Reset download count"


@admin.register(PaymentLog)
class PaymentLogAdmin(admin.ModelAdmin):
    list_display = ['razorpay_payment_id', 'order', 'amount', 'status', 'method', 'created_at']
    list_filter = ['status', 'method', 'created_at']
    search_fields = ['razorpay_payment_id', 'razorpay_order_id', 'order__order_id']
    readonly_fields = ['created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('order')


@admin.register(DownloadLog)
class DownloadLogAdmin(admin.ModelAdmin):
    list_display = ['order_item', 'user', 'ip_address', 'downloaded_at']
    list_filter = ['downloaded_at']
    search_fields = ['order_item__project_title', 'user__username', 'ip_address']
    readonly_fields = ['downloaded_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('order_item', 'user')
