from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView
from django.urls import reverse
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Project, Category, ProjectImage
from orders.models import Order, OrderItem
from .admin_forms import ProjectCreateForm, ProjectUpdateForm, CategoryForm, ProjectImageFormSet
from django.contrib.auth.models import User
import json


def admin_required(user):
    """Check if user is admin/staff"""
    return user.is_authenticated and (user.is_staff or user.is_superuser)


class AdminRequiredMixin(UserPassesTestMixin):
    """Mixin to require admin access"""
    def test_func(self):
        return admin_required(self.request.user)
    
    def handle_no_permission(self):
        messages.error(self.request, 'Access denied. Admin privileges required.')
        return redirect('home')


class AdminDashboardView(AdminRequiredMixin, TemplateView):
    template_name = 'admin/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get date ranges
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        # Order statistics
        total_orders = Order.objects.count()
        pending_orders = Order.objects.filter(status='pending').count()
        processing_orders = Order.objects.filter(status='processing').count()
        completed_orders = Order.objects.filter(status='completed').count()
        
        # Revenue statistics
        total_revenue = Order.objects.filter(payment_status='completed').aggregate(
            total=Sum('total_amount'))['total'] or 0
        week_revenue = Order.objects.filter(
            payment_status='completed', 
            created_at__gte=week_ago
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        month_revenue = Order.objects.filter(
            payment_status='completed', 
            created_at__gte=month_ago
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        # Product statistics
        total_products = Project.objects.count()
        active_products = Project.objects.filter(is_active=True).count()
        inactive_products = Project.objects.filter(is_active=False).count()
        
        # Recent orders
        recent_orders = Order.objects.select_related('user').order_by('-created_at')[:10]
        
        # Top selling products
        top_products = Project.objects.annotate(
            order_count=Count('orderitem')
        ).filter(order_count__gt=0).order_by('-order_count')[:5]
        
        context.update({
            'total_orders': total_orders,
            'pending_orders': pending_orders,
            'processing_orders': processing_orders,
            'completed_orders': completed_orders,
            'total_revenue': total_revenue,
            'week_revenue': week_revenue,
            'month_revenue': month_revenue,
            'total_products': total_products,
            'active_products': active_products,
            'inactive_products': inactive_products,
            'recent_orders': recent_orders,
            'top_products': top_products,
        })
        
        return context


class AdminOrderListView(AdminRequiredMixin, ListView):
    model = Order
    template_name = 'admin/orders/order_list.html'
    context_object_name = 'orders'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Order.objects.select_related('user').order_by('-created_at')
        
        # Filter by status
        status = self.request.GET.get('status')
        if status and status != 'all':
            queryset = queryset.filter(status=status)
        
        # Filter by payment status
        payment_status = self.request.GET.get('payment_status')
        if payment_status and payment_status != 'all':
            queryset = queryset.filter(payment_status=payment_status)
        
        # Search
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(order_id__icontains=search) |
                Q(customer_name__icontains=search) |
                Q(customer_email__icontains=search) |
                Q(user__username__icontains=search)
            )
        
        # Date filter
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        
        if date_from:
            try:
                date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
                queryset = queryset.filter(created_at__date__gte=date_from)
            except ValueError:
                pass
        
        if date_to:
            try:
                date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
                queryset = queryset.filter(created_at__date__lte=date_to)
            except ValueError:
                pass
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Order.STATUS_CHOICES
        context['payment_status_choices'] = Order.PAYMENT_STATUS_CHOICES
        context['current_status'] = self.request.GET.get('status', 'all')
        context['current_payment_status'] = self.request.GET.get('payment_status', 'all')
        context['search_query'] = self.request.GET.get('search', '')
        context['date_from'] = self.request.GET.get('date_from', '')
        context['date_to'] = self.request.GET.get('date_to', '')
        return context


class AdminOrderDetailView(AdminRequiredMixin, DetailView):
    model = Order
    template_name = 'admin/orders/order_detail.html'
    context_object_name = 'order'
    slug_field = 'order_id'
    slug_url_kwarg = 'order_id'
    
    def get_queryset(self):
        return Order.objects.select_related('user').prefetch_related('items__project')


@login_required
@user_passes_test(admin_required)
@require_POST
def update_order_status(request, order_id):
    order = get_object_or_404(Order, order_id=order_id)
    new_status = request.POST.get('status')
    admin_notes = request.POST.get('admin_notes', '')
    
    if new_status in dict(Order.STATUS_CHOICES):
        old_status = order.status
        order.status = new_status
        if admin_notes:
            order.admin_notes = admin_notes
        order.save()
        
        messages.success(request, f'Order status updated from {old_status} to {new_status}')
        
        # Auto-update delivery status for order items
        if new_status == 'completed':
            order.items.update(delivery_status='delivered')
    else:
        messages.error(request, 'Invalid status')
    
    return redirect('admin_panel:order_detail', order_id=order_id)


class AdminProductListView(AdminRequiredMixin, ListView):
    model = Project
    template_name = 'admin/products/product_list.html'
    context_object_name = 'products'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Project.objects.select_related('category', 'created_by').order_by('-created_at')
        
        # Filter by category
        category = self.request.GET.get('category')
        if category and category != 'all':
            queryset = queryset.filter(category_id=category)
        
        # Filter by status
        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)
        
        # Search
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(tags__icontains=search)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['current_category'] = self.request.GET.get('category', 'all')
        context['current_status'] = self.request.GET.get('status', 'all')
        context['search_query'] = self.request.GET.get('search', '')
        # Average price across the full filtered queryset (not just current page)
        try:
            qs = self.get_queryset()
            context['avg_price'] = qs.aggregate(avg=Avg('price'))['avg'] or 0
        except Exception:
            context['avg_price'] = 0
        return context


class AdminProductCreateView(AdminRequiredMixin, CreateView):
    model = Project
    form_class = ProjectCreateForm
    template_name = 'admin/products/product_create.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = ProjectImageFormSet(self.request.POST, self.request.FILES, instance=self.object)
        else:
            context['formset'] = ProjectImageFormSet(instance=None)
        return context
    
    def post(self, request, *args, **kwargs):
        self.object = None
        form = self.get_form()
        formset = ProjectImageFormSet(self.request.POST, self.request.FILES, instance=self.object)
        
        if form.is_valid():
            return self.form_valid(form, formset)
        else:
            return self.form_invalid(form, formset)
    
    def form_valid(self, form, formset):
        form.instance.created_by = self.request.user
        self.object = form.save()
        
        # Only save formset if it's valid and has data
        if formset.is_valid():
            formset.instance = self.object
            # Only save forms that have actual data
            for form_instance in formset:
                if form_instance.cleaned_data and not form_instance.cleaned_data.get('DELETE', False):
                    if form_instance.cleaned_data.get('image') or form_instance.cleaned_data.get('image_url'):
                        form_instance.save()
        
        messages.success(self.request, f'Product "{self.object.title}" created successfully!')
        return redirect(self.get_success_url())
    
    def form_invalid(self, form, formset):
        print("Form validation failed:")
        if not form.is_valid():
            print("Main form errors:", form.errors)
        if not formset.is_valid():
            print("Formset errors:", formset.errors)
            print("Formset non-form errors:", formset.non_form_errors())
        
        return self.render_to_response(
            self.get_context_data(form=form, formset=formset)
        )
    
    def get_success_url(self):
        return f'/admin-panel/products/{self.object.id}/edit/'


class AdminProductUpdateView(AdminRequiredMixin, UpdateView):
    model = Project
    form_class = ProjectUpdateForm
    template_name = 'admin/products/product_edit.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = ProjectImageFormSet(self.request.POST, self.request.FILES, instance=self.object)
        else:
            context['formset'] = ProjectImageFormSet(instance=self.object)
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        
        if formset.is_valid():
            self.object = form.save()
            formset.instance = self.object
            formset.save()
            messages.success(self.request, f'Product "{form.instance.title}" updated successfully!')
            return redirect(self.get_success_url())
        else:
            return self.render_to_response(self.get_context_data(form=form))
    
    def get_success_url(self):
        return f'/admin-panel/products/{self.object.id}/edit/'


@login_required
@user_passes_test(admin_required)  
@require_POST
def toggle_product_status(request, product_id):
    product = get_object_or_404(Project, id=product_id)
    product.is_active = not product.is_active
    product.save()
    
    status_text = 'activated' if product.is_active else 'deactivated'
    messages.success(request, f'Product "{product.title}" {status_text}')
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'is_active': product.is_active,
            'message': f'Product {status_text}'
        })
    
    return redirect('admin_panel:product_list')


@login_required
@user_passes_test(admin_required)
@require_POST
def delete_product(request, product_id):
    product = get_object_or_404(Project, id=product_id)
    title = product.title
    product.delete()
    
    messages.success(request, f'Product "{title}" deleted successfully!')
    return redirect('admin_panel:product_list')


@login_required
@user_passes_test(admin_required)
@require_POST
def delete_gallery_image(request, image_id):
    """Delete a gallery image via AJAX"""
    try:
        image = get_object_or_404(ProjectImage, id=image_id)
        image.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


class AdminCategoryListView(AdminRequiredMixin, ListView):
    model = Category
    template_name = 'admin/categories/category_list.html'
    context_object_name = 'categories'
    
    def get_queryset(self):
        return Category.objects.annotate(project_count=Count('projects'))


class AdminCategoryCreateView(AdminRequiredMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = 'admin/categories/category_create.html'
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Category "{form.instance.name}" created successfully!')
        return response
    
    def get_success_url(self):
        return '/admin-panel/categories/'


class AdminCategoryUpdateView(AdminRequiredMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = 'admin/categories/category_edit.html'
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Category "{form.instance.name}" updated successfully!')
        return response
    
    def get_success_url(self):
        return '/admin-panel/categories/'


@login_required
@user_passes_test(admin_required)
@require_POST
def delete_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    
    # Check if category has products
    if category.projects.count() > 0:
        messages.error(request, f'Cannot delete category "{category.name}" because it has {category.projects.count()} products associated with it.')
        return redirect('admin_panel:category_list')
    
    name = category.name
    category.delete()
    
    messages.success(request, f'Category "{name}" deleted successfully!')
    return redirect('admin_panel:category_list')


@login_required
@user_passes_test(admin_required)
def admin_analytics(request):
    """Analytics view with charts and statistics"""
    context = {
        'title': 'Real-time Analytics',
    }
    return render(request, 'admin/analytics.html', context)


@login_required
@user_passes_test(admin_required)
def analytics_api(request):
    """API endpoint for real-time analytics data"""
    from django.http import JsonResponse
    # Dates for charts and comparisons
    today = timezone.now().date()
    last_30_days = [today - timedelta(days=x) for x in range(29, -1, -1)]
    total_revenue = Order.objects.filter(
        payment_status='completed'
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    total_orders = Order.objects.count()
    total_products = Project.objects.count()
    total_users = User.objects.count()
    
    # Recent orders (last 5)
    recent_orders = Order.objects.select_related('user').order_by('-created_at')[:5]
    recent_orders_data = []
    for order in recent_orders:
        recent_orders_data.append({
            'order_id': str(order.order_id)[:8],
            'order_id_full': str(order.order_id),
            'customer_name': order.customer_name,
            'total_amount': float(order.total_amount),
            'created_at': order.created_at.strftime('%Y-%m-%d %H:%M'),
            'status': order.status,
            'detail_url': reverse('admin_panel:order_detail', kwargs={'order_id': order.order_id})
        })
    
    # Top products (by order count)
    top_products = Project.objects.annotate(
        orders_count=Count('orderitem')
    ).filter(orders_count__gt=0).order_by('-orders_count')[:5]
    
    top_products_data = []
    for product in top_products:
        top_products_data.append({
            'title': product.title,
            'id': product.id,
            'slug': product.slug,
            'category': product.category.name if product.category else 'Uncategorized',
            'price': float(product.price),
            'orders_count': product.orders_count,
            'image_url': product.get_featured_image_url() if hasattr(product, 'get_featured_image_url') else None,
            'detail_url': reverse('project_detail', args=[product.slug]),
            'admin_edit_url': reverse('admin_panel:product_edit', kwargs={'pk': product.id})
        })
    
    # Daily revenue for last 30 days
    daily_revenue = []
    for date in last_30_days:
        revenue = Order.objects.filter(
            created_at__date=date,
            payment_status='completed'
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        daily_revenue.append({
            'date': date.strftime('%Y-%m-%d'),
            'revenue': float(revenue)
        })
    
    # Order status distribution
    status_data = []
    for status_code, status_name in Order.STATUS_CHOICES:
        count = Order.objects.filter(status=status_code).count()
        if count > 0:  # Only include statuses with orders
            status_data.append({
                'status': status_name,
                'count': count
            })
    
    # Top selling categories
    category_data = []
    categories = Category.objects.annotate(
        order_count=Count('projects__orderitem')
    ).filter(order_count__gt=0).order_by('-order_count')[:5]
    
    for category in categories:
        category_data.append({
            'name': category.name,
            'orders': category.order_count
        })
    
    # Calculate additional metrics
    avg_order_value = Order.objects.filter(
        payment_status='completed'
    ).aggregate(avg=Avg('total_amount'))['avg'] or 0
    
    # Get current and last month ranges
    first_of_this_month = today.replace(day=1)
    last_month_end = first_of_this_month - timedelta(days=1)
    first_of_last_month = last_month_end.replace(day=1)

    # Orders MoM
    this_month_orders = Order.objects.filter(
        created_at__date__gte=first_of_this_month
    ).count()
    last_month_orders = Order.objects.filter(
        created_at__date__gte=first_of_last_month,
        created_at__date__lte=last_month_end
    ).count()
    order_growth = 0.0
    if last_month_orders > 0:
        order_growth = ((this_month_orders - last_month_orders) / last_month_orders) * 100.0

    # Products new this month
    try:
        products_new_this_month = Project.objects.filter(
            created_at__date__gte=first_of_this_month
        ).count()
    except Exception:
        # If Project doesn't have created_at, default to 0 new
        products_new_this_month = 0

    # Users MoM growth (based on date_joined)
    this_month_users = User.objects.filter(
        date_joined__date__gte=first_of_this_month
    ).count()
    last_month_users = User.objects.filter(
        date_joined__date__gte=first_of_last_month,
        date_joined__date__lte=last_month_end
    ).count()
    users_growth = 0.0
    if last_month_users > 0:
        users_growth = ((this_month_users - last_month_users) / last_month_users) * 100.0

    # Revenue MoM (completed payments only)
    this_month_revenue = Order.objects.filter(
        payment_status='completed',
        created_at__date__gte=first_of_this_month
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    last_month_revenue = Order.objects.filter(
        payment_status='completed',
        created_at__date__gte=first_of_last_month,
        created_at__date__lte=last_month_end
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    revenue_growth = 0.0
    if last_month_revenue and last_month_revenue > 0:
        revenue_growth = ((this_month_revenue - last_month_revenue) / last_month_revenue) * 100.0
    
    # Conversion rate (assuming 1000 visitors per month as example)
    conversion_rate = (this_month_orders / 1000) * 100 if this_month_orders > 0 else 0
    
    data = {
        'key_metrics': {
            'total_revenue': float(total_revenue),
            'total_orders': total_orders,
            'total_products': total_products,
            'total_users': total_users,
            'avg_order_value': float(avg_order_value),
            'order_growth': round(order_growth, 1),
            'revenue_growth': round(revenue_growth, 1),
            'products_new_this_month': products_new_this_month,
            'users_growth': round(users_growth, 1),
            'conversion_rate': round(conversion_rate, 2),
            'return_rate': 3.2  # Static for now
        },
        'charts': {
            'daily_revenue': daily_revenue,
            'status_distribution': status_data,
            'category_orders': category_data
        },
        'recent_orders': recent_orders_data,
        'top_products': top_products_data,
        'last_updated': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    return JsonResponse(data)
