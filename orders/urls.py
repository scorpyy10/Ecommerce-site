from django.urls import path
from . import views

urlpatterns = [
# Checkout process
    path('delivery-info/', views.DeliveryInfoView.as_view(), name='delivery_info'),
    path('checkout/', views.CheckoutView.as_view(), name='checkout'),
    path('create-payment/', views.create_razorpay_order, name='create_payment'),
    path('payment/callback/', views.payment_callback, name='payment_callback'),
    path('payment/success/', views.PaymentSuccessView.as_view(), name='payment_success'),
    path('payment/failed/', views.PaymentFailedView.as_view(), name='payment_failed'),
    
    # Order management
    path('my-orders/', views.OrderListView.as_view(), name='order_list'),
    path('order/<uuid:order_id>/', views.OrderDetailView.as_view(), name='order_detail'),
    path('download/<int:item_id>/', views.download_file, name='download_file'),
    
    # Order tracking
    path('track/<uuid:order_id>/', views.track_order, name='track_order'),
]
