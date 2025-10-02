#!/usr/bin/env python3
"""
Test Enhanced Matching with Real Qogita Data
Tests the enhanced matching system with a few real products from Qogita API
"""

import json
import sys
from typing import List, Dict

# Add current directory to path
sys.path.append('.')

from core.qogita_api import QogitaAPI
from utils.enhanced_gtin_processor import EnhancedGTINProcessor
from utils.product_matcher import ProductMatcher, QogitaProduct
from core.keepa_api import KeepaAPI
from core.enhanced_roi_calculator import EnhancedROICalculator

def load_config():
    """Load configuration"""
    try:
        with open('config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("ERROR: config.json not found. Please create it from config.json.example")
        return None

def test_with_real_qogita_data():
    """Test enhanced matching with real Qogita products"""
    print("=== Testing Enhanced Matching with Real Qogita Data ===")
    
    # Load configuration
    config = load_config()
    if not config:
        return False
    
    # Initialize APIs
    try:
        qogita_api = QogitaAPI(config)
        keepa_api = KeepaAPI(config)
        calculator = EnhancedROICalculator()
        matcher = ProductMatcher(keepa_api, calculator)
        gtin_processor = EnhancedGTINProcessor()
        
        print("All APIs initialized successfully")
    except Exception as e:
        print(f"Error initializing APIs: {e}")
        return False
    
    # Get some real products from Qogita
    try:
        print("\nFetching L'Oréal products from Qogita...")
        products = qogita_api.search_products("L'Oréal", limit=3)
        
        if not products:
            print("No products found from Qogita")
            return False
        
        print(f"Found {len(products)} L'Oréal products")
        
    except Exception as e:
        print(f"Error fetching Qogita products: {e}")
        return False
    
    # Test enhanced matching on real products
    for i, product_data in enumerate(products, 1):
        print(f"\n--- Testing Real Product {i}/{len(products)} ---")
        
        # Convert to QogitaProduct format
        qogita_product = QogitaProduct(
            gtin=product_data.get('gtin', ''),
            name=product_data.get('name', ''),
            category=product_data.get('category', ''),
            brand=product_data.get('brand', ''),
            wholesale_price=float(product_data.get('price', 0)),
            unit=product_data.get('unit', 'piece'),
            stock=int(product_data.get('stock', 0)),
            suppliers=int(product_data.get('suppliers', 0)),
            product_url=product_data.get('url', ''),
            image_url=product_data.get('image_url', '')
        )
        
        print(f"GTIN: {qogita_product.gtin}")
        print(f"Brand: {qogita_product.brand}")
        print(f"Name: {qogita_product.name}")
        print(f"Wholesale Price: €{qogita_product.wholesale_price:.2f}")
        print(f"Stock: {qogita_product.stock}")
        
        # Test GTIN processing
        if qogita_product.gtin:
            gtin_result = gtin_processor.process_gtin(qogita_product.gtin)
            print(f"GTIN Valid: {gtin_result['is_valid']}, Confidence: {gtin_result['confidence']}%")
            if gtin_result['search_variants']:
                print(f"Search Variants: {gtin_result['search_variants']}")
        
        # Test enhanced matching
        try:
            matched_product = matcher.match_single_product(qogita_product)
            
            print(f"Match Status: {matched_product.match_status}")
            print(f"Match Confidence: {matched_product.match_confidence}%")
            
            if matched_product.amazon_asin:
                print(f"✅ Amazon ASIN: {matched_product.amazon_asin}")
                if matched_product.amazon_price:
                    print(f"Amazon Price: €{matched_product.amazon_price:.2f}")
                    if matched_product.profit_margin is not None:
                        print(f"Profit Margin: €{matched_product.profit_margin:.2f}")
                    if matched_product.roi_percentage is not None:
                        print(f"ROI: {matched_product.roi_percentage:.1f}%")
            else:
                print(f"❌ No Amazon match found")
                
        except Exception as e:
            print(f"Error matching product: {e}")
    
    return True

def main():
    """Run real data test"""
    print("Enhanced Matching System - Real Data Test")
    print("=" * 50)
    
    try:
        if test_with_real_qogita_data():
            print("\n" + "=" * 50)
            print("Real data test completed successfully!")
            return True
        else:
            print("Real data test failed!")
            return False
            
    except Exception as e:
        print(f"Test failed with error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
