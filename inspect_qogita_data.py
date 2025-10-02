"""
Debug script to inspect Qogita data structure
"""

import logging
import sys
import os

# Configure logging
logging.basicConfig(level=logging.INFO)

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.qogita_api import QogitaAPI
from utils.config import Config


def inspect_qogita_data():
    """Inspect the actual structure of Qogita data"""
    print("🔍 Inspecting Qogita Data Structure")
    print("=" * 40)
    
    try:
        # Initialize API
        config = Config()
        qogita_settings = config.get('qogita_settings', {})
        qogita_email = qogita_settings.get('email')
        qogita_password = qogita_settings.get('password')
        
        if not qogita_email or not qogita_password:
            print("❌ Qogita credentials not found")
            return
        
        qogita_api = QogitaAPI(qogita_email, qogita_password)
        
        # Get a small sample of products
        print("📥 Fetching L'Oréal products...")
        raw_products = qogita_api.search_products_by_brand("L'Oréal")
        
        if not raw_products:
            print("❌ No products found")
            return
            
        print(f"✅ Found {len(raw_products)} products")
        
        # Inspect first few products
        print("\n📊 Sample Product Data:")
        for i, product in enumerate(raw_products[:5]):
            print(f"\n--- Product {i+1} ---")
            for key, value in product.items():
                print(f"{key}: {repr(value)}")
        
        # Check field names
        if raw_products:
            print(f"\n📋 Available Fields: {list(raw_products[0].keys())}")
            
        # Count products with GTIN
        gtin_count = 0
        price_count = 0
        valid_count = 0
        
        for product in raw_products:
            gtin = product.get('GTIN', '').strip()
            price_str = product.get('€ Lowest Price inc. shipping', '').strip()
            
            if gtin:
                gtin_count += 1
            if price_str:
                try:
                    price = float(price_str)
                    if price > 0:
                        price_count += 1
                        if gtin:
                            valid_count += 1
                except ValueError:
                    pass
        
        print(f"\n📈 Data Quality:")
        print(f"Products with GTIN: {gtin_count}/{len(raw_products)} ({gtin_count/len(raw_products)*100:.1f}%)")
        print(f"Products with valid price: {price_count}/{len(raw_products)} ({price_count/len(raw_products)*100:.1f}%)")
        print(f"Products with both GTIN & price: {valid_count}/{len(raw_products)} ({valid_count/len(raw_products)*100:.1f}%)")
        
        # Show some valid products if any
        if valid_count > 0:
            print(f"\n✅ Sample Valid Products:")
            count = 0
            for product in raw_products:
                gtin = product.get('GTIN', '').strip()
                price_str = product.get('€ Lowest Price inc. shipping', '').strip()
                
                if gtin and price_str:
                    try:
                        price = float(price_str)
                        if price > 0:
                            name = product.get('Name', 'N/A')
                            print(f"  {count+1}. {name[:60]}...")
                            print(f"     GTIN: {gtin}")
                            print(f"     Price: €{price}")
                            count += 1
                            if count >= 3:
                                break
                    except ValueError:
                        continue
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    inspect_qogita_data()
