from django.urls import path
from . import admin_views

app_name = 'admin_panel'

urlpatterns = [
    # Dashboard
    path('', admin_views.AdminDashboardView.as_view(), name='dashboard'),
    path('analytics/', admin_views.admin_analytics, name='analytics'),
    path('api/analytics/', admin_views.analytics_api, name='analytics_api'),
    
    # Orders
    path('orders/', admin_views.AdminOrderListView.as_view(), name='order_list'),
    path('orders/<uuid:order_id>/', admin_views.AdminOrderDetailView.as_view(), name='order_detail'),
    path('orders/<uuid:order_id>/update-status/', admin_views.update_order_status, name='update_order_status'),
    
    # Products
    path('products/', admin_views.AdminProductListView.as_view(), name='product_list'),
    path('products/create/', admin_views.AdminProductCreateView.as_view(), name='product_create'),
    path('products/<int:pk>/edit/', admin_views.AdminProductUpdateView.as_view(), name='product_edit'),
    path('products/<int:product_id>/toggle/', admin_views.toggle_product_status, name='toggle_product_status'),
    path('products/<int:product_id>/delete/', admin_views.delete_product, name='delete_product'),
    path('products/images/<int:image_id>/delete/', admin_views.delete_gallery_image, name='delete_gallery_image'),
    
    # Categories
    path('categories/', admin_views.AdminCategoryListView.as_view(), name='category_list'),
    path('categories/create/', admin_views.AdminCategoryCreateView.as_view(), name='category_create'),
    path('categories/<int:pk>/edit/', admin_views.AdminCategoryUpdateView.as_view(), name='category_edit'),
    path('categories/<int:category_id>/delete/', admin_views.delete_category, name='category_delete'),
]
