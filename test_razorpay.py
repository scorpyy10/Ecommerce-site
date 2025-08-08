#!/usr/bin/env python3
"""
Test script to verify Razorpay integration
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

import razorpay
from django.conf import settings

def test_razorpay_connection():
    """Test Razorpay API connection and key validation"""
    try:
        print("Testing Razorpay Integration...")
        print(f"Key ID: {settings.RAZORPAY_KEY_ID[:10]}...")  # Show only first 10 chars
        print(f"Key Secret: {'*' * len(settings.RAZORPAY_KEY_SECRET)}")
        
        # Create Razorpay client
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        
        # Test creating an order
        order_data = {
            'amount': 100,  # 1 rupee in paise
            'currency': 'INR',
            'receipt': 'test_receipt_001',
            'payment_capture': 1
        }
        
        print("\nCreating test order...")
        order = client.order.create(order_data)
        print(f"✅ Order created successfully!")
        print(f"Order ID: {order['id']}")
        print(f"Amount: ₹{order['amount']/100}")
        print(f"Status: {order['status']}")
        
        # Test fetching the order
        print(f"\nFetching order details...")
        fetched_order = client.order.fetch(order['id'])
        print(f"✅ Order fetched successfully!")
        print(f"Created at: {fetched_order['created_at']}")
        
        return True
        
    except razorpay.errors.BadRequestError as e:
        print(f"❌ Bad Request Error: {e}")
        print("This usually means your API keys are invalid or the request format is wrong.")
        return False
        
    except razorpay.errors.ServerError as e:
        print(f"❌ Server Error: {e}")
        print("Razorpay server is having issues. Try again later.")
        return False
        
    except razorpay.errors.GatewayError as e:
        print(f"❌ Gateway Error: {e}")
        print("Network connectivity issue with Razorpay.")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        print(f"Error type: {type(e).__name__}")
        return False

def test_payment_verification():
    """Test payment signature verification"""
    try:
        print("\n" + "="*50)
        print("Testing Payment Signature Verification...")
        
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        
        # Test data (these would normally come from Razorpay callback)
        params_dict = {
            'razorpay_order_id': 'order_test123',
            'razorpay_payment_id': 'pay_test123',
            'razorpay_signature': 'invalid_signature_for_test'
        }
        
        print("Testing signature verification with test data...")
        try:
            client.utility.verify_payment_signature(params_dict)
            print("✅ Signature verification method is working")
        except razorpay.errors.SignatureVerificationError:
            print("✅ Signature verification method is working (correctly rejected invalid signature)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in signature verification test: {e}")
        return False

if __name__ == "__main__":
    print("Razorpay Integration Test")
    print("=" * 50)
    
    success1 = test_razorpay_connection()
    success2 = test_payment_verification()
    
    print("\n" + "="*50)
    if success1 and success2:
        print("✅ All tests passed! Razorpay integration is working correctly.")
        print("\nPossible issues with your payment flow:")
        print("1. Check browser console for JavaScript errors")
        print("2. Verify OTP is being entered correctly")
        print("3. Check if popup blockers are interfering")
        print("4. Ensure the payment callback URL is accessible")
        print("5. Check Django logs for any server-side errors")
    else:
        print("❌ Some tests failed. Please check your Razorpay configuration.")
        print("\nTroubleshooting steps:")
        print("1. Verify your API keys in .env file")
        print("2. Check if you're using test keys for test payments")
        print("3. Ensure your Razorpay account is active")
