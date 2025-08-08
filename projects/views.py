from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, TemplateView
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .models import Project, Category, Cart, CartItem


class HomeView(TemplateView):
    template_name = 'projects/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['featured_projects'] = Project.objects.filter(is_active=True)[:8]
        context['categories'] = Category.objects.all()[:6]
        return context


class ProjectListView(ListView):
    model = Project
    template_name = 'projects/project_list.html'
    context_object_name = 'projects'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Project.objects.filter(is_active=True).select_related('category')
        
        # Filter by category
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category__slug=category)
        
        # Filter by price range
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        
        # Sort
        sort_by = self.request.GET.get('sort', '-created_at')
        if sort_by in ['price', '-price', 'title', '-title', 'created_at', '-created_at']:
            queryset = queryset.order_by(sort_by)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['current_category'] = self.request.GET.get('category')
        context['current_sort'] = self.request.GET.get('sort', '-created_at')
        return context


class ProjectDetailView(DetailView):
    model = Project
    template_name = 'projects/project_detail.html'
    context_object_name = 'project'
    
    def get_queryset(self):
        return Project.objects.filter(is_active=True).select_related('category').prefetch_related('images')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['related_projects'] = Project.objects.filter(
            category=self.object.category, 
            is_active=True
        ).exclude(id=self.object.id)[:4]
        return context


class CategoryView(ListView):
    model = Project
    template_name = 'projects/category_projects.html'
    context_object_name = 'projects'
    paginate_by = 12
    
    def get_queryset(self):
        self.category = get_object_or_404(Category, slug=self.kwargs['slug'])
        return Project.objects.filter(category=self.category, is_active=True)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        return context


class SearchView(ListView):
    model = Project
    template_name = 'projects/search_results.html'
    context_object_name = 'projects'
    paginate_by = 12
    
    def get_queryset(self):
        query = self.request.GET.get('q')
        if query:
            return Project.objects.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(tags__icontains=query) |
                Q(category__name__icontains=query),
                is_active=True
            ).select_related('category')
        return Project.objects.none()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        return context


class CartView(TemplateView):
    template_name = 'projects/cart.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart = self.get_cart()
        context['cart'] = cart
        context['cart_items'] = cart.items.all() if cart else []
        return context
    
    def get_cart(self):
        if not self.request.session.session_key:
            self.request.session.create()
        
        if self.request.user.is_authenticated:
            cart, created = Cart.objects.get_or_create(user=self.request.user)
        else:
            cart, created = Cart.objects.get_or_create(session_key=self.request.session.session_key)
        
        return cart


def get_or_create_cart(request):
    """Helper function to get or create cart"""
    if not request.session.session_key:
        request.session.create()
    
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        cart, created = Cart.objects.get_or_create(session_key=request.session.session_key)
    
    return cart


@require_POST
def add_to_cart(request, project_id):
    project = get_object_or_404(Project, id=project_id, is_active=True)
    cart = get_or_create_cart(request)
    
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        project=project,
        defaults={'quantity': 1}
    )
    
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    
    messages.success(request, f'{project.title} added to cart!')
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f'{project.title} added to cart!',
            'cart_count': cart.get_total_items()
        })
    
    return redirect('cart')


@require_POST
def remove_from_cart(request, item_id):
    cart = get_or_create_cart(request)
    cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
    
    project_title = cart_item.project.title
    cart_item.delete()
    
    messages.success(request, f'{project_title} removed from cart!')
    return redirect('cart')


@require_POST
def update_cart_item(request, item_id):
    cart = get_or_create_cart(request)
    cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
    
    quantity = int(request.POST.get('quantity', 1))
    if quantity > 0:
        cart_item.quantity = quantity
        cart_item.save()
        messages.success(request, 'Cart updated!')
    else:
        cart_item.delete()
        messages.success(request, f'{cart_item.project.title} removed from cart!')
    
    return redirect('cart')


@require_POST
def clear_cart(request):
    cart = get_or_create_cart(request)
    cart.items.all().delete()
    messages.success(request, 'Cart cleared!')
    return redirect('cart')
