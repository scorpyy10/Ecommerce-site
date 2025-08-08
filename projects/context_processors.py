from .models import Cart, Category

def cart_context(request):
    """
    Context processor to make cart information available in all templates
    """
    cart_items_count = 0
    cart_total = 0
    
    if request.session.session_key:
        try:
            if request.user.is_authenticated:
                cart = Cart.objects.filter(user=request.user).first()
            else:
                cart = Cart.objects.filter(session_key=request.session.session_key).first()
            
            if cart:
                cart_items_count = cart.get_total_items()
                cart_total = cart.get_total_price()
        except:
            pass
    
    return {
        'cart_items_count': cart_items_count,
        'cart_total': cart_total,
    }


def categories_context(request):
    """
    Context processor to make categories available in all templates
    """
    try:
        categories = Category.objects.all()[:6]  # Limit to 6 categories for navigation
    except:
        categories = []
    
    return {
        'nav_categories': categories,
    }
