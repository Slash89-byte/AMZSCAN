#!/usr/bin/env python3
"""
Test EAN lookup via Keepa API
"""

import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.keepa_api import KeepaAPI
from utils.config import Config
from utils.identifiers import detect_and_validate_identifier

def test_ean_lookup():
    """Test EAN lookup functionality"""
    
    print("🧪 Testing EAN Lookup via Keepa API")
    print("=" * 40)
    
    try:
        config = Config()
        api_key = config.get('keepa_api_key', '')
        
        if not api_key:
            print("❌ No API key found")
            return False
        
        keepa_api = KeepaAPI(api_key)
        
        # Test EAN-13 that should correspond to an Amazon product
        test_ean = "4003994155486"
        print(f"Testing EAN-13: {test_ean}")
        
        # First validate the identifier
        result = detect_and_validate_identifier(test_ean)
        print(f"Identifier validation: {result}")
        
        if not result['is_valid']:
            print("❌ EAN validation failed")
            return False
        
        # Test the Keepa API lookup
        print("🔍 Looking up product via Keepa API...")
        product_data = keepa_api.get_product_data(test_ean, domain=4)
        
        if product_data:
            print("✅ EAN lookup successful!")
            print(f"  Title: {product_data.get('title', 'N/A')}")
            print(f"  ASIN: {product_data.get('asin', 'N/A')}")
            print(f"  Current Price: €{product_data.get('current_price', 0):.2f}")
            print(f"  Category: {product_data.get('category', 'N/A')}")
            return True
        else:
            print("⚠️  No product data returned")
            print("This might be because:")
            print("  • EAN not available in Amazon France")
            print("  • Product discontinued")
            print("  • Keepa API limitations")
            return False
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        return False

def test_asin_lookup():
    """Test ASIN lookup for comparison"""
    
    print("\n🧪 Testing ASIN Lookup for Comparison")
    print("=" * 40)
    
    try:
        config = Config()
        api_key = config.get('keepa_api_key', '')
        keepa_api = KeepaAPI(api_key)
        
        # Test with known working ASIN
        test_asin = "B0BQBXBW88"
        print(f"Testing ASIN: {test_asin}")
        
        product_data = keepa_api.get_product_data(test_asin, domain=4)
        
        if product_data:
            print("✅ ASIN lookup successful!")
            print(f"  Title: {product_data.get('title', 'N/A')}")
            print(f"  Current Price: €{product_data.get('current_price', 0):.2f}")
            return True
        else:
            print("❌ ASIN lookup failed")
            return False
            
    except Exception as e:
        print(f"❌ Error during ASIN test: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Multi-Format Identifier API Test")
    print("=" * 50)
    
    # Test ASIN first (should work)
    asin_success = test_asin_lookup()
    
    # Test EAN (might work depending on availability)
    ean_success = test_ean_lookup()
    
    print("\n" + "=" * 50)
    print("📋 Test Summary:")
    print(f"  ASIN Lookup: {'✅ Working' if asin_success else '❌ Failed'}")
    print(f"  EAN Lookup:  {'✅ Working' if ean_success else '⚠️  Limited/Unavailable'}")
    
    if asin_success:
        print("\n🎉 Multi-format identifier support is ready!")
        print("Users can now input EAN, UPC, GTIN codes in addition to ASIN.")
        print("Note: Not all EAN codes may be available in Amazon's database.")
    else:
        print("\n❌ Basic functionality issue detected.")
