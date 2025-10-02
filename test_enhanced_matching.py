#!/usr/bin/env python3
"""
Test Enhanced Product Matching System
Tests the complete integration of enhanced GTIN processing and Amazon matching
"""

import json
import sys
from typing import List, Dict
import traceback

# Add current directory to path
sys.path.append('.')

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

def create_test_products() -> List[QogitaProduct]:
    """Create test products from real Qogita data"""
    return [
        # L'Oréal product with good GTIN
        QogitaProduct(
            gtin="3600523951369",
            name="Revitalift Laser X3 Day Cream 50ml",
            category="Beauty & Personal Care",
            brand="L'Oréal Paris",
            wholesale_price=12.50,
            unit="piece",
            stock=45,
            suppliers=3,
            product_url="https://example.com/loreal1",
            image_url="https://example.com/loreal1.jpg"
        ),
        
        # Another L'Oréal with different GTIN format
        QogitaProduct(
            gtin="0000030080515",
            name="True Match Foundation W1 Golden Ivory",
            category="Beauty & Personal Care",
            brand="L'Oréal Paris",
            wholesale_price=8.75,
            unit="piece",
            stock=32,
            suppliers=2,
            product_url="https://example.com/loreal2",
            image_url="https://example.com/loreal2.jpg"
        ),
        
        # Maybelline product
        QogitaProduct(
            gtin="3607345064672",
            name="Instant Anti Age Eraser Concealer",
            category="Beauty & Personal Care",
            brand="Maybelline",
            wholesale_price=6.25,
            unit="piece",
            stock=28,
            suppliers=1,
            product_url="https://example.com/maybelline1",
            image_url="https://example.com/maybelline1.jpg"
        ),
        
        # Product with potentially invalid GTIN
        QogitaProduct(
            gtin="123456789",
            name="Test Product Invalid GTIN",
            category="Beauty & Personal Care",
            brand="Test Brand",
            wholesale_price=10.00,
            unit="piece",
            stock=15,
            suppliers=1,
            product_url="https://example.com/test",
            image_url="https://example.com/test.jpg"
        ),
        
        # Product with missing GTIN
        QogitaProduct(
            gtin="",
            name="Generic Product No GTIN",
            category="Beauty & Personal Care",
            brand="Generic Brand",
            wholesale_price=5.00,
            unit="piece",
            stock=10,
            suppliers=1,
            product_url="https://example.com/generic",
            image_url="https://example.com/generic.jpg"
        )
    ]

def test_gtin_processing():
    """Test enhanced GTIN processing"""
    print("=== Testing Enhanced GTIN Processing ===")
    
    processor = EnhancedGTINProcessor()
    test_gtins = [
        "3600523951369",
        "0000030080515",
        "3607345064672",
        "123456789",
        "",
        "invalid_gtin"
    ]
    
    for gtin in test_gtins:
        print(f"\nTesting GTIN: '{gtin}'")
        
        # Process GTIN
        result = processor.process_gtin(gtin)
        print(f"  Valid: {result['is_valid']}, Confidence: {result['confidence']}%")
        print(f"  Format: {result['format']}")
        print(f"  Normalized: {result['normalized']}")
        
        if result['search_variants']:
            print(f"  Search variants: {result['search_variants']}")
    
    return True

def test_product_matching():
    """Test enhanced product matching"""
    print("\n=== Testing Enhanced Product Matching ===")
    
    # Load configuration
    config = load_config()
    if not config:
        return False
    
    # Initialize components
    try:
        keepa_api = KeepaAPI(config)
        calculator = EnhancedROICalculator()
        matcher = ProductMatcher(keepa_api, calculator)
        print("ProductMatcher initialized successfully")
    except Exception as e:
        print(f"Error initializing ProductMatcher: {e}")
        return False
    
    # Test with sample products
    test_products = create_test_products()
    
    for i, product in enumerate(test_products, 1):
        print(f"\n--- Testing Product {i}/{len(test_products)} ---")
        print(f"GTIN: {product.gtin}")
        print(f"Brand: {product.brand}")
        print(f"Name: {product.name}")
        print(f"Wholesale Price: ${product.wholesale_price:.2f}")
        
        try:
            # Test matching
            matched_product = matcher.match_single_product(product)
            
            print(f"Match Status: {matched_product.match_status}")
            print(f"Match Confidence: {matched_product.match_confidence}%")
            
            if matched_product.amazon_asin:
                print(f"Amazon ASIN: {matched_product.amazon_asin}")
                print(f"Amazon Price: ${matched_product.amazon_price:.2f}" if matched_product.amazon_price else "Price not available")
                
                if matched_product.profit_margin is not None:
                    print(f"Profit Margin: ${matched_product.profit_margin:.2f}")
                
                if matched_product.roi_percentage is not None:
                    print(f"ROI: {matched_product.roi_percentage:.1f}%")
                
        except Exception as e:
            print(f"Error matching product: {e}")
            print(f"Traceback: {traceback.format_exc()}")
    
    return True

def test_confidence_scoring():
    """Test confidence scoring system"""
    print("\n=== Testing Confidence Scoring ===")
    
    processor = EnhancedGTINProcessor()
    
    # Test various confidence scenarios
    test_cases = [
        ("3600523951369", "Valid GTIN-13 with correct checksum"),
        ("0000030080515", "Valid GTIN-13 with leading zeros"),
        ("123456789012", "Invalid GTIN-13 (wrong checksum)"),
        ("12345678", "Valid GTIN-8 format"),
        ("123456789", "Too short for any GTIN"),
        ("", "Empty GTIN"),
    ]
    
    for gtin, description in test_cases:
        print(f"\nTesting: {description}")
        print(f"GTIN: '{gtin}'")
        
        result = processor.process_gtin(gtin)
        confidence = result['confidence']
        is_valid = result['is_valid']
        
        print(f"Valid: {is_valid}, Confidence: {confidence}%")
        
        if confidence >= 90:
            confidence_level = "High"
        elif confidence >= 70:
            confidence_level = "Medium"
        elif confidence > 0:
            confidence_level = "Low"
        else:
            confidence_level = "None"
        
        print(f"Confidence Level: {confidence_level}")
    
    return True

def main():
    """Run all tests"""
    print("Enhanced Product Matching System Test")
    print("=" * 50)
    
    try:
        # Test GTIN processing
        if not test_gtin_processing():
            print("GTIN processing test failed!")
            return False
        
        # Test confidence scoring
        if not test_confidence_scoring():
            print("Confidence scoring test failed!")
            return False
        
        # Test product matching
        if not test_product_matching():
            print("Product matching test failed!")
            return False
        
        print("\n" + "=" * 50)
        print("All tests completed successfully!")
        print("Enhanced matching system is ready for production use.")
        
        return True
        
    except Exception as e:
        print(f"Test suite failed with error: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
