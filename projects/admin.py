from django.contrib import admin
from .models import Category, Project, ProjectImage, Cart, CartItem


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at']


class ProjectImageInline(admin.TabularInline):
    model = ProjectImage
    extra = 1
    fields = ['image', 'image_url', 'alt_text', 'order']
    
    def get_readonly_fields(self, request, obj=None):
        readonly_fields = []
        # Show preview of the current image URL
        return readonly_fields


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'price', 'is_active', 'created_by', 'created_at']
    list_filter = ['category', 'is_active', 'delivery_type', 'created_at']
    search_fields = ['title', 'description', 'tags']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['created_at', 'updated_at']
    inlines = [ProjectImageInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'description', 'category', 'tags')
        }),
        ('Pricing & Status', {
            'fields': ('price', 'is_active')
        }),
        ('Media', {
            'fields': ('featured_image', 'featured_image_url', 'demo_video_url')
        }),
        ('Delivery', {
            'fields': ('delivery_type', 'download_file', 'download_url')
        }),
        ('SEO', {
            'fields': ('meta_description',),
            'classes': ['collapse']
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ['collapse']
        })
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ProjectImage)
class ProjectImageAdmin(admin.ModelAdmin):
    list_display = ['project', 'alt_text', 'order']
    list_filter = ['project']
    search_fields = ['project__title', 'alt_text']


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ['added_at']


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'session_key', 'get_total_items', 'get_total_price', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'session_key']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [CartItemInline]
    
    def get_total_items(self, obj):
        return obj.get_total_items()
    get_total_items.short_description = 'Total Items'
    
    def get_total_price(self, obj):
        return f"₹{obj.get_total_price():.2f}"
    get_total_price.short_description = 'Total Price'


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['cart', 'project', 'quantity', 'get_total_price', 'added_at']
    list_filter = ['added_at']
    search_fields = ['project__title', 'cart__user__username']
    readonly_fields = ['added_at']
    
    def get_total_price(self, obj):
        return f"₹{obj.get_total_price():.2f}"
    get_total_price.short_description = 'Total Price'
