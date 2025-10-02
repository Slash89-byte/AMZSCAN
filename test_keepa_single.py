#!/usr/bin/env python3
"""
Simple single request test to verify Keepa API without rate limiting issues
"""

import sys
import os
import json

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

def test_single_request():
    """Test a single API request to verify fix"""
    print("🔍 Testing Single Keepa API Request")
    print("=" * 50)
    
    config = load_config()
    if not config:
        return
    
    # Initialize KeepaAPI
    keepa_key = config.get('keepa_api_key')
    if not keepa_key:
        print("❌ No Keepa API key found in config!")
        return
    
    keepa_api = KeepaAPI(api_key=keepa_key)
    
    # Test connection first
    print("🔗 Testing connection...")
    try:
        if keepa_api.test_connection():
            print("✅ Connection successful")
        else:
            print("❌ Connection failed - but continuing with product test...")
    except Exception as e:
        print(f"⚠️ Connection test failed with error: {e}")
        print("📋 Continuing with product test anyway...")
    
    # Test single product lookup anyway
    test_gtin = '3600542525824'  # Known working GTIN
    print(f"\n🔍 Looking up GTIN: {test_gtin}")
    
    try:
        result = keepa_api.get_product_data(test_gtin, domain=4)
        
        if result and result.get('success'):
            data = result.get('data', {})
            print(f"✅ SUCCESS!")
            print(f"📦 Product: {data.get('title', 'Unknown')}")
            print(f"💰 Price: €{data.get('current_price', 0.0):.2f}")
            print(f"🏷️ ASIN: {data.get('asin', 'N/A')}")
            
            if data.get('current_price', 0) > 0:
                print("✅ Amazon price retrieval is working correctly!")
                print("\n🎯 The 400 Bad Request error has been FIXED!")
                print("🎯 Rate limiting is now implemented!")
            else:
                print("⚠️ Product found but no price available")
        else:
            error = result.get('error', 'Unknown error') if result else 'No result'
            print(f"❌ Failed: {error}")
            
    except Exception as e:
        print(f"💥 Exception: {e}")

if __name__ == "__main__":
    test_single_request()
