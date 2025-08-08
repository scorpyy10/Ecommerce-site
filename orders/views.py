from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView, ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
from django.utils import timezone
from django.urls import reverse
from projects.models import Cart, CartItem
from .models import Order, OrderItem, PaymentLog, DownloadLog
from .forms import AddressForm
import razorpay
import json
import uuid


class DeliveryInfoView(LoginRequiredMixin, TemplateView):
    template_name = 'orders/delivery_info.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart = self.get_cart()
        
        if not cart or not cart.items.exists():
            messages.error(self.request, 'Your cart is empty. Please add items before checkout.')
            return context
        
        context['cart'] = cart
        context['cart_items'] = cart.items.all()
        context['form'] = AddressForm(user=self.request.user)
        return context
    
    def post(self, request, *args, **kwargs):
        cart = self.get_cart()
        
        if not cart or not cart.items.exists():
            messages.error(request, 'Your cart is empty. Please add items before checkout.')
            return redirect('cart')
        
        form = AddressForm(request.POST, user=request.user)
        
        if form.is_valid():
            # Store address data in session for later use
            address_data = {
                'delivery_first_name': form.cleaned_data['delivery_first_name'],
                'delivery_last_name': form.cleaned_data['delivery_last_name'],
                'delivery_company': form.cleaned_data['delivery_company'],
                'delivery_address_line_1': form.cleaned_data['delivery_address_line_1'],
                'delivery_address_line_2': form.cleaned_data['delivery_address_line_2'],
                'delivery_city': form.cleaned_data['delivery_city'],
                'delivery_state': form.cleaned_data['delivery_state'],
                'delivery_postal_code': form.cleaned_data['delivery_postal_code'],
                'delivery_country': form.cleaned_data['delivery_country'],
                'delivery_phone': form.cleaned_data['delivery_phone'],
                'delivery_instructions': form.cleaned_data['delivery_instructions'],
                'preferred_delivery_time': form.cleaned_data['preferred_delivery_time'],
            }
            request.session['address_data'] = address_data
            return redirect('checkout')
        else:
            context = self.get_context_data(**kwargs)
            context['form'] = form
            return self.render_to_response(context)
    
    def get_cart(self):
        if self.request.user.is_authenticated:
            return Cart.objects.filter(user=self.request.user).first()
        return None


class CheckoutView(LoginRequiredMixin, TemplateView):
    template_name = 'orders/checkout.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart = self.get_cart()
        
        if not cart or not cart.items.exists():
            messages.error(self.request, 'Your cart is empty. Please add items before checkout.')
            return context
        
        # Check if address data is in session
        address_data = self.request.session.get('address_data')
        if not address_data:
            messages.error(self.request, 'Please provide delivery information first.')
            context['redirect_to_delivery'] = True
            return context
        
        context['cart'] = cart
        context['cart_items'] = cart.items.all()
        context['address_data'] = address_data
        context['razorpay_key_id'] = settings.RAZORPAY_KEY_ID
        return context
    
    def get_cart(self):
        if self.request.user.is_authenticated:
            return Cart.objects.filter(user=self.request.user).first()
        return None


@login_required
@require_POST
def create_razorpay_order(request):
    try:
        cart = Cart.objects.filter(user=request.user).first()
        if not cart or not cart.items.exists():
            return JsonResponse({'error': 'Cart is empty'}, status=400)
        
        # Get address data from session
        address_data = request.session.get('address_data')
        if not address_data:
            return JsonResponse({'error': 'Delivery information is required'}, status=400)
        
        # Create Razorpay client
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        
        # Calculate total amount
        total_amount = cart.get_total_price()
        amount_in_paise = int(total_amount * 100)
        
        # Create order in database with address data
        order = Order.objects.create(
            user=request.user,
            total_amount=total_amount,
            customer_name=request.user.get_full_name() or request.user.username,
            customer_email=request.user.email,
            customer_phone=request.user.username,  # You might want to add phone to User model
            **address_data  # Unpack all address fields
        )
        
        # Create order items
        for cart_item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                project=cart_item.project,
                project_title=cart_item.project.title,
                project_price=cart_item.project.price,
                quantity=cart_item.quantity
            )
        
        # Create Razorpay order
        razorpay_order = client.order.create({
            'amount': amount_in_paise,
            'currency': 'INR',
            'receipt': str(order.order_id),
            'payment_capture': 1
        })
        
        # Update order with Razorpay order ID
        order.razorpay_order_id = razorpay_order['id']
        order.save()
        
        return JsonResponse({
            'order_id': razorpay_order['id'],
            'amount': amount_in_paise,
            'currency': 'INR',
            'name': 'Devam Project',
            'description': f'Order #{order.order_id}',
            'prefill': {
                'name': order.customer_name,
                'email': order.customer_email,
            }
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def payment_callback(request):
    if request.method == 'POST':
        try:
            # Get payment details from request
            payment_id = request.POST.get('razorpay_payment_id')
            order_id = request.POST.get('razorpay_order_id')
            signature = request.POST.get('razorpay_signature')
            
            # Debug logging
            print(f"Payment callback received:")
            print(f"Payment ID: {payment_id}")
            print(f"Order ID: {order_id}")
            print(f"Signature: {signature}")
            
            # Check if this is an AJAX request
            is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
            
            # Debug logging
            print(f"Request headers: {dict(request.headers)}")
            print(f"Is AJAX request: {is_ajax}")
            print(f"Content-Type: {request.headers.get('Content-Type', 'Not set')}")
            print(f"X-Requested-With: {request.headers.get('X-Requested-With', 'Not set')}")
            
            if not all([payment_id, order_id, signature]):
                error_msg = 'Missing payment information'
                if is_ajax:
                    return JsonResponse({'success': False, 'error': error_msg}, status=400)
                messages.error(request, error_msg)
                return redirect('payment_failed')
            
            # Verify payment signature
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            
            params_dict = {
                'razorpay_order_id': order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            }
            
            # Verify signature
            try:
                client.utility.verify_payment_signature(params_dict)
                print("Payment signature verified successfully")
            except Exception as verify_error:
                print(f"Signature verification failed: {verify_error}")
                error_msg = 'Payment signature verification failed'
                if is_ajax:
                    return JsonResponse({'success': False, 'error': error_msg}, status=400)
                messages.error(request, error_msg)
                return redirect('payment_failed')
            
            # Update order status
            try:
                order = Order.objects.get(razorpay_order_id=order_id)
                print(f"Found order: {order.order_id}")
            except Order.DoesNotExist:
                print(f"Order not found for razorpay_order_id: {order_id}")
                error_msg = 'Order not found'
                if is_ajax:
                    return JsonResponse({'success': False, 'error': error_msg}, status=404)
                messages.error(request, error_msg)
                return redirect('payment_failed')
            
            order.razorpay_payment_id = payment_id
            order.razorpay_signature = signature
            order.payment_status = 'completed'
            order.status = 'processing'
            order.save()
            print(f"Order {order.order_id} updated successfully")
            
            # Log payment
            PaymentLog.objects.create(
                order=order,
                razorpay_payment_id=payment_id,
                razorpay_order_id=order_id,
                amount=order.total_amount,
                status='captured'
            )
            print("Payment log created")
            
            # Clear cart and session data
            Cart.objects.filter(user=order.user).delete()
            print("Cart cleared")
            
            # Clear address data from session
            if 'address_data' in request.session:
                del request.session['address_data']
            
            # Store order ID in session for success page
            request.session['last_order_id'] = str(order.order_id)
            
            # Force session save to ensure all changes are persisted
            request.session.save()
            print(f"Order ID stored in session: {order.order_id}")
            print("Session saved successfully")
            
            # Return appropriate response
            if is_ajax:
                return JsonResponse({
                    'success': True, 
                    'message': 'Payment successful! Your order has been confirmed.',
                    'redirect_url': reverse('payment_success')
                })
            else:
                return redirect('payment_success')
            
        except Exception as e:
            print(f"Payment callback error: {str(e)}")
            print(f"Error type: {type(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            error_msg = f'Payment verification failed: {str(e)}'
            
            if is_ajax:
                return JsonResponse({'success': False, 'error': error_msg}, status=500)
            messages.error(request, error_msg)
            return redirect('payment_failed')
    
    print(f"Payment callback received non-POST request: {request.method}")
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)
    return redirect('payment_failed')


class PaymentSuccessView(LoginRequiredMixin, TemplateView):
    template_name = 'orders/payment_success.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Try to get order from session first
        last_order_id = self.request.session.get('last_order_id')
        order = None
        
        if last_order_id:
            try:
                order = Order.objects.get(
                    order_id=last_order_id,
                    user=self.request.user,
                    payment_status='completed'
                )
                # Clear the session after using it
                del self.request.session['last_order_id']
            except Order.DoesNotExist:
                pass
        
        # Fallback to most recent order
        if not order:
            order = Order.objects.filter(
                user=self.request.user,
                payment_status='completed'
            ).order_by('-created_at').first()
        
        if order:
            context['order'] = order
        else:
            # Fallback in case no order is found
            messages.error(self.request, 'Order information not found.')
        
        return context


class PaymentFailedView(LoginRequiredMixin, TemplateView):
    template_name = 'orders/payment_failed.html'


class OrderListView(LoginRequiredMixin, ListView):
    model = Order
    template_name = 'orders/order_list.html'
    context_object_name = 'orders'
    paginate_by = 10
    
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by('-created_at')


class OrderDetailView(LoginRequiredMixin, DetailView):
    model = Order
    template_name = 'orders/order_detail.html'
    context_object_name = 'order'
    slug_field = 'order_id'
    slug_url_kwarg = 'order_id'
    
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)


@login_required
def download_file(request, item_id):
    order_item = get_object_or_404(OrderItem, id=item_id, order__user=request.user)
    
    # Check if user can download
    if not order_item.can_download():
        messages.error(request, 'Download not available or limit exceeded.')
        return redirect('order_detail', order_id=order_item.order.order_id)
    
    # Log the download
    DownloadLog.objects.create(
        order_item=order_item,
        user=request.user,
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )
    
    # Increment download count
    order_item.download_count += 1
    order_item.save()
    
    # Return file or redirect to download URL
    if order_item.delivery_file:
        # Serve file download
        response = HttpResponse(order_item.delivery_file.read(), content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{order_item.project_title}.zip"'
        return response
    elif order_item.delivery_url:
        return redirect(order_item.delivery_url)
    else:
        messages.error(request, 'Download file not available.')
        return redirect('order_detail', order_id=order_item.order.order_id)


@login_required
def track_order(request, order_id):
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    return render(request, 'orders/track_order.html', {'order': order})
