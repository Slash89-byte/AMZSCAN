"""
Test script for the complete Qogita + Amazon matching workflow
"""

import logging
import sys
import os

# Configure logging
logging.basicConfig(level=logging.INFO)

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.qogita_api import QogitaAPI
from core.keepa_api import KeepaAPI
from core.enhanced_roi_calculator import EnhancedROICalculator
from utils.product_matcher import ProductMatcher, QogitaProduct
from utils.config import Config


def test_complete_workflow():
    """Test the complete workflow: Qogita -> Matching -> Profitability"""
    print("🧪 Testing Complete Qogita + Amazon Workflow")
    print("=" * 50)
    
    try:
        # Initialize APIs
        config = Config()
        
        # Get Qogita credentials from config
        qogita_settings = config.get('qogita_settings', {})
        qogita_email = qogita_settings.get('email')
        qogita_password = qogita_settings.get('password')
        
        if not qogita_email or not qogita_password:
            print("❌ Qogita credentials not found in config.json")
            print("Please add qogita_settings with email and password to config.json")
            return
        
        qogita_api = QogitaAPI(qogita_email, qogita_password)
        
        # Get Keepa API key from config
        keepa_api_key = config.get('keepa_api_key')
        if not keepa_api_key:
            print("❌ Keepa API key not found in config.json")
            return
            
        keepa_api = KeepaAPI(keepa_api_key)
        roi_calculator = EnhancedROICalculator()
        product_matcher = ProductMatcher(keepa_api, roi_calculator)
        
        print("✅ APIs initialized successfully")
        
        # Test with a small brand to avoid rate limits
        test_brand = "L'Oréal"
        print(f"🔍 Testing with brand: {test_brand}")
        
        # Get products from Qogita
        print("📥 Fetching products from Qogita...")
        raw_products = qogita_api.search_products_by_brand(test_brand)
        
        if not raw_products:
            print("❌ No products found from Qogita")
            return
            
        print(f"✅ Found {len(raw_products)} products from Qogita")
        
        # Convert to QogitaProduct objects (find valid ones)
        qogita_products = []
        for i, product_data in enumerate(raw_products):
            try:
                gtin = str(product_data.get('gtin', '')).strip()
                price = product_data.get('wholesale_price', 0)
                
                # Skip products without GTIN or price
                if not gtin or price <= 0:
                    continue
                
                qogita_product = QogitaProduct(
                    gtin=gtin,
                    name=product_data.get('name', ''),
                    category=product_data.get('category', ''),
                    brand=product_data.get('brand', ''),
                    wholesale_price=float(price),
                    unit=str(product_data.get('unit', '')),
                    stock=int(product_data.get('stock_quantity', 0)),
                    suppliers=int(product_data.get('supplier_count', 0)),
                    product_url=product_data.get('product_url', ''),
                    image_url=product_data.get('image_url', '')
                )
                
                qogita_products.append(qogita_product)
                print(f"  📦 Product {len(qogita_products)}: {qogita_product.name[:50]}... (€{qogita_product.wholesale_price:.2f}) GTIN: {qogita_product.gtin}")
                
                # Stop after finding 3 valid products for testing
                if len(qogita_products) >= 3:
                    break
                    
            except (ValueError, KeyError) as e:
                continue
        
        if not qogita_products:
            print("❌ No valid products to match")
            return
            
        print(f"✅ Converted {len(qogita_products)} products for matching")
        
        # Test matching with Amazon
        print("\n🔗 Matching with Amazon data...")
        matched_products = []
        
        for i, qogita_product in enumerate(qogita_products):
            print(f"  🔍 Matching product {i+1}: {qogita_product.gtin}")
            
            matched_product = product_matcher.match_single_product(qogita_product)
            matched_products.append(matched_product)
            
            print(f"    Status: {matched_product.match_status}")
            if matched_product.amazon_price:
                print(f"    Amazon Price: €{matched_product.amazon_price:.2f}")
                print(f"    ROI: {matched_product.roi_percentage:.1f}%" if matched_product.roi_percentage else "    ROI: N/A")
            
            # Add delay to respect rate limits
            import time
            time.sleep(2)
        
        # Summary
        print("\n📊 Results Summary:")
        print(f"Total products tested: {len(matched_products)}")
        
        matched_count = len([p for p in matched_products if p.match_status == "matched"])
        print(f"Successfully matched: {matched_count}")
        
        profitable_count = len([p for p in matched_products 
                               if p.roi_percentage and p.roi_percentage >= 15])
        print(f"Profitable (ROI ≥ 15%): {profitable_count}")
        
        # Show profitable products
        if profitable_count > 0:
            print("\n💰 Profitable Products:")
            for product in matched_products:
                if product.roi_percentage and product.roi_percentage >= 15:
                    qp = product.qogita_product
                    print(f"  ✅ {qp.name[:40]}...")
                    print(f"      Wholesale: €{qp.wholesale_price:.2f} | Amazon: €{product.amazon_price:.2f}")
                    print(f"      Profit: €{product.profit_margin:.2f} | ROI: {product.roi_percentage:.1f}%")
                    print(f"      ASIN: {product.amazon_asin}")
        
        print("\n🎉 Test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_complete_workflow()
