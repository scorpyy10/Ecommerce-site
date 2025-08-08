from django.db import models
from django.contrib.auth.models import User
from projects.models import Project
import uuid
from django.utils import timezone


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    # Order identification
    order_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    
    # Order details
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Payment details
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=200, blank=True, null=True)
    
    # Customer details
    customer_name = models.CharField(max_length=200)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=20, blank=True)
    
    # Delivery address
    delivery_first_name = models.CharField(max_length=100, blank=True)
    delivery_last_name = models.CharField(max_length=100, blank=True)
    delivery_company = models.CharField(max_length=200, blank=True)
    delivery_address_line_1 = models.CharField(max_length=255, blank=True)
    delivery_address_line_2 = models.CharField(max_length=255, blank=True)
    delivery_city = models.CharField(max_length=100, blank=True)
    delivery_state = models.CharField(max_length=100, blank=True)
    delivery_postal_code = models.CharField(max_length=20, blank=True)
    delivery_country = models.CharField(max_length=100, default='India')
    delivery_phone = models.CharField(max_length=20, blank=True)
    
    # Additional delivery preferences
    delivery_instructions = models.TextField(blank=True, help_text="Special delivery instructions")
    preferred_delivery_time = models.CharField(
        max_length=50, 
        choices=[
            ('morning', 'Morning (9 AM - 12 PM)'),
            ('afternoon', 'Afternoon (12 PM - 5 PM)'),
            ('evening', 'Evening (5 PM - 8 PM)'),
            ('anytime', 'Anytime')
        ], 
        default='anytime'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Notes
    notes = models.TextField(blank=True)
    admin_notes = models.TextField(blank=True, help_text="Internal notes for admin")
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['payment_status']),
        ]
    
    def save(self, *args, **kwargs):
        if self.status == 'completed' and not self.completed_at:
            self.completed_at = timezone.now()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Order {self.order_id} - {self.user.username}"
    
    def get_total_items(self):
        return sum(item.quantity for item in self.items.all())
    
    def get_delivery_name(self):
        """Get formatted delivery name"""
        if self.delivery_first_name or self.delivery_last_name:
            return f"{self.delivery_first_name} {self.delivery_last_name}".strip()
        return self.customer_name
    
    def get_delivery_address(self):
        """Get formatted delivery address"""
        address_parts = []
        
        if self.delivery_company:
            address_parts.append(self.delivery_company)
        
        if self.delivery_address_line_1:
            address_parts.append(self.delivery_address_line_1)
        
        if self.delivery_address_line_2:
            address_parts.append(self.delivery_address_line_2)
        
        city_state_postal = []
        if self.delivery_city:
            city_state_postal.append(self.delivery_city)
        if self.delivery_state:
            city_state_postal.append(self.delivery_state)
        if self.delivery_postal_code:
            city_state_postal.append(self.delivery_postal_code)
        
        if city_state_postal:
            address_parts.append(", ".join(city_state_postal))
        
        if self.delivery_country:
            address_parts.append(self.delivery_country)
        
        return "\n".join(address_parts)
    
    def has_delivery_address(self):
        """Check if delivery address is provided"""
        return bool(self.delivery_address_line_1 and self.delivery_city and self.delivery_postal_code)


class OrderItem(models.Model):
    DELIVERY_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
    ]
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    
    # Item details (stored at time of purchase)
    project_title = models.CharField(max_length=200)
    project_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    
    # Delivery details
    delivery_status = models.CharField(max_length=20, choices=DELIVERY_STATUS_CHOICES, default='pending')
    delivery_url = models.URLField(blank=True, help_text="Download link for customer")
    delivery_file = models.FileField(upload_to='orders/deliveries/', blank=True, null=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    
    # Access control
    download_count = models.PositiveIntegerField(default=0)
    max_downloads = models.PositiveIntegerField(default=5)
    access_expires_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['order', 'project']
    
    def get_total_price(self):
        return self.project_price * self.quantity
    
    def can_download(self):
        if self.delivery_status != 'delivered':
            return False
        if self.download_count >= self.max_downloads:
            return False
        if self.access_expires_at and timezone.now() > self.access_expires_at:
            return False
        return True
    
    def __str__(self):
        return f"{self.project_title} x {self.quantity} - Order {self.order.order_id}"


class PaymentLog(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payment_logs')
    razorpay_payment_id = models.CharField(max_length=100)
    razorpay_order_id = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=50)
    method = models.CharField(max_length=50, blank=True)
    response_data = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Payment {self.razorpay_payment_id} - {self.status}"


class DownloadLog(models.Model):
    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE, related_name='download_logs')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    downloaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-downloaded_at']
    
    def __str__(self):
        return f"Download {self.order_item.project_title} by {self.user.username}"
