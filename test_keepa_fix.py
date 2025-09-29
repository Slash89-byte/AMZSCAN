#!/usr/bin/env python3
"""
Quick test to verify the Keepa API fix
"""

import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.keepa_api import KeepaAPI
from utils.config import Config

def test_keepa_fix():
    """Test the Keepa API fix"""
    
    print("🔧 Testing Keepa API Fix")
    print("=" * 30)
    
    try:
        config = Config()
        api_key = config.get('keepa_api_key', '')
        
        if not api_key:
            print("❌ No API key found")
            return
        
        keepa_api = KeepaAPI(api_key)
        
        # Test with our known ASIN
        asin = "B0BQBXBW88"
        print(f"Testing ASIN: {asin}")
        
        product_data = keepa_api.get_product_data(asin, domain=4)
        
        if product_data:
            print(f"✅ Product data retrieved")
            print(f"  Title: {product_data.get('title', 'N/A')}")
            print(f"  Current Price: €{product_data.get('current_price', 0)}")
            print(f"  Sales Rank: {product_data.get('sales_rank', 'N/A')}")
            print(f"  Category: {product_data.get('category', 'N/A')}")
            print(f"  In Stock: {product_data.get('in_stock', False)}")
            
            if product_data.get('current_price', 0) > 0:
                print("🎉 SUCCESS: Price data is now working!")
                return True
            else:
                print("❌ Still no price data")
                return False
        else:
            print("❌ No product data returned")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_keepa_fix()
    
    if success:
        print("\n✅ Keepa API fix successful!")
        print("The buy box price reading issue has been resolved.")
    else:
        print("\n❌ Issue still exists")
