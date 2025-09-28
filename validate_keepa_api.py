"""
Real API validation test for Keepa API integration
This script helps validate the Keepa API integration with better error handling
"""

from core.keepa_api import KeepaAPI
from utils.config import Config
import json

def test_keepa_api_validation():
    """Test Keepa API with comprehensive validation"""
    
    print("🔍 Testing Keepa API Integration Validation")
    print("=" * 50)
    
    # Load config
    config = Config()
    api_key = config.get_keepa_api_key()
    
    if not api_key:
        print("❌ No Keepa API key found in config.json")
        print("ℹ️  Please add your API key to config.json")
        return False
    
    print(f"✅ API key found: {api_key[:8]}...")
    
    # Initialize API
    keepa_api = KeepaAPI(api_key)
    
    # Test connection first
    print("\n📡 Testing API connection...")
    connection_ok = keepa_api.test_connection()
    
    if not connection_ok:
        print("❌ API connection failed!")
        print("   • Check your API key")
        print("   • Check your internet connection")
        print("   • Verify Keepa API subscription status")
        return False
    
    print("✅ API connection successful!")
    
    # Test with a known ASIN (confirmed available in French marketplace)
    test_asin = "B0D8L8HYWM"  # Real ASIN available in France
    print(f"\n🔍 Testing product data retrieval for ASIN: {test_asin}")
    
    product_data = keepa_api.get_product_data(test_asin)
    
    if not product_data:
        print("❌ No product data returned!")
        print("   Possible causes:")
        print("   • Invalid ASIN")
        print("   • Product not available in France marketplace")
        print("   • API rate limit exceeded")
        print("   • Temporary API issue")
        return False
    
    print("✅ Product data retrieved successfully!")
    
    # Validate data completeness
    print("\n📊 Validating product data completeness...")
    
    required_fields = ['asin', 'title', 'current_price']
    optional_fields = ['sales_rank', 'review_count', 'rating', 'category', 'weight', 'in_stock']
    
    missing_required = []
    for field in required_fields:
        if field not in product_data or product_data[field] is None:
            missing_required.append(field)
    
    if missing_required:
        print(f"❌ Missing required fields: {missing_required}")
        return False
    
    print("✅ All required fields present")
    
    # Check data quality
    print("\n🎯 Checking data quality...")
    
    issues = []
    
    # Check current price
    current_price = product_data.get('current_price', 0)
    if current_price <= 0:
        issues.append("Current price is zero or negative")
    
    # Check title
    title = product_data.get('title', '')
    if not title or title == 'Unknown Product' or len(title) < 5:
        issues.append("Product title is empty or too short")
    
    # Check weight (should be reasonable)
    weight = product_data.get('weight', 0)
    if weight <= 0 or weight > 50:  # Most products are 0.1kg to 50kg
        issues.append(f"Weight seems unrealistic: {weight}kg")
    
    if issues:
        print("⚠️  Data quality issues found:")
        for issue in issues:
            print(f"   • {issue}")
        print("   The data might still be usable, but double-check results.")
    else:
        print("✅ Data quality looks good!")
    
    # Display sample data
    print("\n📋 Sample product data:")
    print(f"   ASIN: {product_data.get('asin', 'N/A')}")
    print(f"   Title: {product_data.get('title', 'N/A')[:50]}...")
    print(f"   Price: €{product_data.get('current_price', 0):.2f}")
    print(f"   Weight: {product_data.get('weight', 0):.2f}kg")
    print(f"   Sales Rank: {product_data.get('sales_rank', 'N/A')}")
    print(f"   Reviews: {product_data.get('review_count', 0)}")
    print(f"   Rating: {product_data.get('rating', 0):.1f}/5.0")
    print(f"   Category: {product_data.get('category', 'Unknown')}")
    print(f"   In Stock: {product_data.get('in_stock', False)}")
    
    return True

def validate_api_response_structure():
    """Test different API response scenarios"""
    
    print("\n🧪 Testing API response validation...")
    
    keepa_api = KeepaAPI("test_key")
    
    # Test 1: Empty product data
    try:
        result = keepa_api._parse_product_data({})
        print("✅ Empty product data handled gracefully")
    except Exception as e:
        print(f"❌ Empty product data caused error: {e}")
    
    # Test 2: Minimal product data
    try:
        minimal_product = {
            "asin": "TEST123",
            "title": "Test Product"
        }
        result = keepa_api._parse_product_data(minimal_product)
        print("✅ Minimal product data handled gracefully")
        print(f"   Price: €{result['current_price']:.2f}")
        print(f"   Category: {result['category']}")
    except Exception as e:
        print(f"❌ Minimal product data caused error: {e}")
    
    # Test 3: Malformed category data
    try:
        malformed_product = {
            "asin": "TEST123",
            "title": "Test Product",
            "categoryTree": ["Electronics", {"name": "Computers"}, None, 12345]
        }
        result = keepa_api._parse_product_data(malformed_product)
        print("✅ Malformed category data handled gracefully")
        print(f"   Category: {result['category']}")
    except Exception as e:
        print(f"❌ Malformed category data caused error: {e}")

if __name__ == "__main__":
    print("🚀 Keepa API Validation Test Suite")
    print("=" * 60)
    
    # Test API response structure handling
    validate_api_response_structure()
    
    # Test real API if key is available
    print("\n" + "=" * 60)
    real_api_success = test_keepa_api_validation()
    
    print("\n" + "=" * 60)
    if real_api_success:
        print("🎉 All validation tests passed!")
        print("   Your Keepa API integration is working correctly.")
    else:
        print("⚠️  Some validation tests failed.")
        print("   Please check your API key and configuration.")
    
    print("\n💡 Next steps:")
    print("   1. Test with different ASINs")
    print("   2. Monitor API usage limits")
    print("   3. Handle rate limiting in production")
    print("=" * 60)
