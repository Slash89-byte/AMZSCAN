#!/usr/bin/env python3
"""
Debug script for testing the fixed Keepa API implementation
"""

import sys
import os
import json
import time

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.keepa_api import KeepaAPI
from utils.enhanced_gtin_processor import EnhancedGTINProcessor

def load_config():
    """Load API configuration"""
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    if not os.path.exists(config_path):
        print("❌ config.json not found!")
        return None
    
    with open(config_path, 'r') as f:
        return json.load(f)

def test_fixed_amazon_price_retrieval():
    """Test the fixed Amazon price retrieval functionality"""
    print("🔍 Testing FIXED Amazon Price Retrieval")
    print("=" * 50)
    
    config = load_config()
    if not config:
        return
    
    # Initialize KeepaAPI
    keepa_key = config.get('keepa_api_key')
    if not keepa_key:
        print("❌ No Keepa API key found in config!")
        return
    
    gtin_processor = EnhancedGTINProcessor()
    keepa_api = KeepaAPI(api_key=keepa_key)
    
    # Test connection first
    print("🔗 Testing Keepa API connection...")
    if keepa_api.test_connection():
        print("✅ Keepa API connection successful")
    else:
        print("❌ Keepa API connection failed")
        return
    
    # Test cases for Amazon price retrieval
    test_cases = [
        {
            'name': 'French Cosmetics Product',
            'gtin': '3600542525824',  # Garnier product
            'expected_brand': 'Garnier'
        },
        {
            'name': 'Electronics Product',
            'asin': 'B08N5WRWNW',  # Echo Dot
            'expected_brand': 'Amazon'
        }
    ]
    
    for test_case in test_cases:
        print(f"\n📋 Testing: {test_case['name']}")
        print("-" * 30)
        
        # Use GTIN or ASIN
        identifier = test_case.get('gtin') or test_case.get('asin')
        
        try:
            # Test the fixed get_product_data method
            print(f"🔍 Looking up: {identifier}")
            result = keepa_api.get_product_data(identifier, domain=4)  # France domain
            
            print(f"📊 Result type: {type(result)}")
            print(f"📋 Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
            
            if result and result.get('success'):
                data = result.get('data', {})
                print(f"✅ Product found: {data.get('title', 'Unknown')}")
                print(f"💰 Current Price: €{data.get('current_price', 0.0):.2f}")
                print(f"📦 ASIN: {data.get('asin', 'N/A')}")
                print(f"⭐ Rating: {data.get('rating', 'N/A')}")
                print(f"📊 Sales Rank: {data.get('sales_rank', 'N/A')}")
                
                if data.get('current_price', 0) > 0:
                    print("✅ Amazon price retrieval working!")
                else:
                    print("⚠️ No current price found")
                    
            else:
                error = result.get('error', 'Unknown error') if result else 'No result returned'
                print(f"❌ Failed to get product data: {error}")
                print(f"📋 Full result: {result}")
                
        except Exception as e:
            print(f"💥 Exception during test: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("🎯 Fixed Amazon Price Retrieval Test Complete")

def test_real_time_scanning_simulation():
    """Simulate real-time scanning scenarios with fixed API"""
    print("\n🔄 Testing Real-Time Scanning Simulation (FIXED)")
    print("=" * 50)
    
    config = load_config()
    if not config:
        return
    
    keepa_key = config.get('keepa_api_key')
    if not keepa_key:
        print("❌ No Keepa API key found!")
        return
    
    gtin_processor = EnhancedGTINProcessor()
    keepa_api = KeepaAPI(api_key=keepa_key)
    
    # Simulate scanning multiple products in quick succession
    scanned_products = [
        '3600542525824',  # Garnier
        '3338221005311',  # L'Oreal
        '8076809512217',  # Another cosmetics product
    ]
    
    print(f"📱 Simulating real-time scan of {len(scanned_products)} products...")
    successful_retrievals = 0
    
    for i, gtin in enumerate(scanned_products, 1):
        print(f"\n🔍 Scanning product {i}/{len(scanned_products)}: {gtin}")
        
        # Add delay between scans to respect rate limits
        if i > 1:
            print("⏱️ Waiting 2 seconds to respect rate limits...")
            time.sleep(2)
        
        try:
            result = keepa_api.get_product_data(gtin, domain=4)
            
            if result and result.get('success'):
                data = result.get('data', {})
                title = data.get('title', 'Unknown Product')
                price = data.get('current_price', 0.0)
                
                print(f"✅ Found: {title[:50]}{'...' if len(title) > 50 else ''}")
                if price > 0:
                    print(f"💰 Amazon Price: €{price:.2f}")
                    print("✅ Real-time price retrieval successful!")
                    successful_retrievals += 1
                else:
                    print("⚠️ No Amazon price available")
            else:
                error = result.get('error', 'Unknown error') if result else 'No result'
                print(f"❌ Lookup failed: {error}")
                
        except Exception as e:
            print(f"💥 Error during scan: {e}")
    
    print(f"\n📊 Results: {successful_retrievals}/{len(scanned_products)} products with Amazon prices")
    print("✅ Real-time scanning simulation complete!")

if __name__ == "__main__":
    print("🚀 Fixed Keepa API Testing Tool")
    print("===============================")
    
    # Run all tests
    test_fixed_amazon_price_retrieval()
    test_real_time_scanning_simulation()
    
    print("\n🎉 All tests completed!")
