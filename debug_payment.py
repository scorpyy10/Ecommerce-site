#!/usr/bin/env python3
"""
Debug script to test the payment flow step by step
"""
import os
import sys
import django
from pathlib import Path

# Add the project directory to the Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'devam_marketplace.settings')
django.setup()

from django.contrib.auth.models import User
from projects.models import Cart, CartItem, Project
from orders.models import Order, OrderItem
import razorpay
from django.conf import settings

def create_test_user_and_cart():
    """Create a test user and cart for debugging"""
    try:
        print("Creating test user and cart...")
        
        # Create or get test user
        user, created = User.objects.get_or_create(
            username='testuser',
            defaults={
                'email': 'test@example.com',
                'first_name': 'Test',
                'last_name': 'User'
            }
        )
        
        if created:
            user.set_password('testpass123')
            user.save()
            print(f"✅ Created new test user: {user.username}")
        else:
            print(f"✅ Using existing test user: {user.username}")
        
        # Check if we have any projects
        projects = Project.objects.all()[:3]
        if not projects:
            print("❌ No projects found in database. Please add some projects first.")
            return None, None
        
        print(f"Found {len(projects)} projects in database")
        
        # Create or get cart
        cart, created = Cart.objects.get_or_create(user=user)
        
        # Clear existing cart items
        cart.items.all().delete()
        
        # Add test items to cart
        for project in projects:
            CartItem.objects.create(
                cart=cart,
                project=project,
                quantity=1
            )
            print(f"Added {project.title} to cart")
        
        print(f"✅ Cart created with {cart.items.count()} items")
        print(f"Total cart value: ₹{cart.get_total_price()}")
        
        return user, cart
        
    except Exception as e:
        print(f"❌ Error creating test user and cart: {e}")
        return None, None

def test_order_creation(user, cart):
    """Test the order creation process"""
    try:
        print(f"\n{'='*50}")
        print("Testing Order Creation...")
        
        # Create Razorpay client
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        
        # Calculate total amount
        total_amount = cart.get_total_price()
        amount_in_paise = int(total_amount * 100)
        
        print(f"Total amount: ₹{total_amount}")
        print(f"Amount in paise: {amount_in_paise}")
        
        # Test address data
        address_data = {
            'delivery_first_name': 'Test',
            'delivery_last_name': 'User',
            'delivery_company': 'Test Company',
            'delivery_address_line_1': '123 Test Street',
            'delivery_address_line_2': 'Apt 456',
            'delivery_city': 'Test City',
            'delivery_state': 'Test State',
            'delivery_postal_code': '123456',
            'delivery_country': 'India',
            'delivery_phone': '9876543210',
            'delivery_instructions': 'Test delivery instructions',
            'preferred_delivery_time': 'anytime',
        }
        
        # Create order in database
        order = Order.objects.create(
            user=user,
            total_amount=total_amount,
            customer_name=user.get_full_name() or user.username,
            customer_email=user.email,
            customer_phone='9876543210',
            **address_data
        )
        
        print(f"✅ Created order: {order.order_id}")
        
        # Create order items
        for cart_item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                project=cart_item.project,
                project_title=cart_item.project.title,
                project_price=cart_item.project.price,
                quantity=cart_item.quantity
            )
            print(f"Added order item: {cart_item.project.title}")
        
        # Create Razorpay order
        razorpay_order = client.order.create({
            'amount': amount_in_paise,
            'currency': 'INR',
            'receipt': str(order.order_id),
            'payment_capture': 1
        })
        
        print(f"✅ Created Razorpay order: {razorpay_order['id']}")
        
        # Update order with Razorpay order ID
        order.razorpay_order_id = razorpay_order['id']
        order.save()
        
        print(f"✅ Order creation successful!")
        return order, razorpay_order
        
    except Exception as e:
        print(f"❌ Error in order creation: {e}")
        return None, None

def test_payment_simulation(order, razorpay_order):
    """Simulate the payment process"""
    try:
        print(f"\n{'='*50}")
        print("Simulating Payment Process...")
        
        # These would normally come from Razorpay's response
        print(f"Order ID: {razorpay_order['id']}")
        print(f"Amount: ₹{razorpay_order['amount']/100}")
        print(f"Currency: {razorpay_order['currency']}")
        print(f"Receipt: {razorpay_order['receipt']}")
        
        print("\n📝 Frontend JavaScript should show:")
        print(f"   - Order ID: {razorpay_order['id']}")
        print(f"   - Amount: {razorpay_order['amount']} paise")
        print(f"   - Customer: {order.customer_name}")
        print(f"   - Email: {order.customer_email}")
        
        print("\n💡 When user completes payment, these would be returned:")
        print("   - razorpay_payment_id: pay_XXXXXXXXXXXXXX")
        print("   - razorpay_order_id: order_XXXXXXXXXXXXXX")
        print("   - razorpay_signature: generated_signature_hash")
        
        print("\n✅ Payment simulation complete!")
        return True
        
    except Exception as e:
        print(f"❌ Error in payment simulation: {e}")
        return False

def check_common_issues():
    """Check for common issues that might cause payment failures"""
    print(f"\n{'='*50}")
    print("Checking for Common Issues...")
    
    issues_found = []
    
    # Check settings
    if not settings.RAZORPAY_KEY_ID:
        issues_found.append("❌ RAZORPAY_KEY_ID is not set")
    else:
        print(f"✅ RAZORPAY_KEY_ID is set: {settings.RAZORPAY_KEY_ID[:10]}...")
    
    if not settings.RAZORPAY_KEY_SECRET:
        issues_found.append("❌ RAZORPAY_KEY_SECRET is not set")
    else:
        print(f"✅ RAZORPAY_KEY_SECRET is set: {'*' * len(settings.RAZORPAY_KEY_SECRET)}")
    
    # Check if using test keys
    if settings.RAZORPAY_KEY_ID.startswith('rzp_test_'):
        print("✅ Using test keys (good for development)")
    elif settings.RAZORPAY_KEY_ID.startswith('rzp_live_'):
        print("⚠️  Using live keys (make sure this is intentional)")
    else:
        issues_found.append("❌ Invalid Razorpay key format")
    
    # Check DEBUG mode
    if settings.DEBUG:
        print("✅ DEBUG mode is enabled (good for development)")
    else:
        print("⚠️  DEBUG mode is disabled")
    
    return issues_found

if __name__ == "__main__":
    print("Payment Flow Debug Script")
    print("=" * 50)
    
    # Check for common issues first
    issues = check_common_issues()
    
    if issues:
        print(f"\n❌ Found {len(issues)} issues:")
        for issue in issues:
            print(f"   {issue}")
        print("\nPlease fix these issues before proceeding.")
        sys.exit(1)
    
    # Create test data
    user, cart = create_test_user_and_cart()
    if not user or not cart:
        sys.exit(1)
    
    # Test order creation
    order, razorpay_order = test_order_creation(user, cart)
    if not order or not razorpay_order:
        sys.exit(1)
    
    # Test payment simulation
    success = test_payment_simulation(order, razorpay_order)
    
    print(f"\n{'='*50}")
    if success:
        print("✅ All tests passed! Your Razorpay integration should be working.")
        print("\nIf payments are still failing, the issue is likely:")
        print("1. 🔍 JavaScript errors in the browser console")
        print("2. 🚫 Browser popup blockers preventing Razorpay modal")
        print("3. 📱 OTP delivery issues or incorrect OTP entry")
        print("4. 🌐 Network issues during payment")
        print("5. 🏦 Bank server issues or card/account problems")
        print("6. 🔒 3D Secure authentication failing")
        
        print("\n🛠️  Debugging steps:")
        print("1. Open browser developer tools (F12)")
        print("2. Go to Console tab")
        print("3. Try making a payment")
        print("4. Look for any red error messages")
        print("5. Check the Network tab for failed requests")
        print("6. Try with a different browser or incognito mode")
        
    else:
        print("❌ Some tests failed. Please check the errors above.")
        
    # Cleanup
    print(f"\n🧹 Cleaning up test data...")
    if 'order' in locals():
        order.delete()
        print("Deleted test order")
    if 'cart' in locals():
        cart.delete()
        print("Deleted test cart")
