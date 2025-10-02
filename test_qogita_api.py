"""
Test script for Qogita API integration.
This script will help discover the correct API endpoints and validate authentication.
"""

import sys
import os
import json
import logging

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.qogita_api import QogitaAPI, QogitaAPIError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_config():
    """Load configuration from config.json"""
    # Try current directory first, then parent directory
    possible_paths = [
        'config.json',
        os.path.join(os.path.dirname(__file__), 'config.json'),
        os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
    ]
    
    for config_path in possible_paths:
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    logger.info(f"Loading config from: {config_path}")
                    return json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing config.json: {e}")
            return None
    
    logger.error("config.json not found in any of the expected locations")
    return None


def test_qogita_authentication():
    """Test Qogita API authentication"""
    print("=" * 60)
    print("QOGITA API AUTHENTICATION TEST")
    print("=" * 60)
    
    # Load configuration
    config = load_config()
    if not config:
        print("❌ Failed to load configuration")
        return False
    
    # Get Qogita credentials
    qogita_settings = config.get('qogita_settings', {})
    email = qogita_settings.get('email', '')
    password = qogita_settings.get('password', '')
    
    if not email or not password:
        print("❌ Qogita credentials not configured in config.json")
        print("Please update the 'qogita_settings' section with your email and password")
        return False
    
    try:
        # Create API client
        print(f"📧 Email: {email}")
        print("🔐 Password: [HIDDEN]")
        print("\n🔄 Attempting to authenticate...")
        
        api = QogitaAPI(email, password)
        success = api.authenticate()
        
        if success:
            print("✅ Authentication successful!")
            print(f"🔑 Access token received: {api.access_token[:20]}...")
            print(f"🛒 Active cart QID: {api.cart_qid}")
            return True
        else:
            print("❌ Authentication failed")
            return False
            
    except QogitaAPIError as e:
        print(f"❌ Qogita API Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def test_product_search(api: QogitaAPI, test_brands: list):
    """Test product search functionality"""
    print("\n" + "=" * 60)
    print("PRODUCT SEARCH TEST")
    print("=" * 60)
    
    for brand in test_brands:
        print(f"\n🔍 Searching for brand: '{brand}'")
        try:
            products = api.search_products_by_brand(brand, limit=10)
            
            if products:
                print(f"✅ Found {len(products)} products for '{brand}'")
                
                # Display first product details
                first_product = products[0]
                print(f"📦 First product: {first_product.get('name', 'N/A')}")
                print(f"💰 Price: {first_product.get('wholesale_price', 'N/A')} {first_product.get('currency', '')}")
                print(f"🔢 EAN: {first_product.get('ean', 'N/A')}")
                
            else:
                print(f"❌ No products found for '{brand}'")
                
        except Exception as e:
            print(f"❌ Error searching for '{brand}': {e}")


def discover_api_endpoints(api: QogitaAPI):
    """Try to discover available API endpoints"""
    print("\n" + "=" * 60)
    print("API ENDPOINT DISCOVERY")
    print("=" * 60)
    
    test_endpoints = [
        "/products/",
        "/products/search/",
        "/catalog/",
        "/catalog/search/",
        "/search/",
        "/search/products/",
        "/api/products/",
        "/api/catalog/",
        "/api/search/",
        "/brands/",
        "/categories/"
    ]
    
    working_endpoints = []
    
    for endpoint in test_endpoints:
        try:
            print(f"🔍 Testing endpoint: {endpoint}")
            response = api.session.get(f"{api.base_url}{endpoint}")
            
            if response.status_code == 200:
                print(f"✅ {endpoint} - Status: {response.status_code}")
                working_endpoints.append(endpoint)
            elif response.status_code == 401:
                print(f"🔐 {endpoint} - Authentication required (Status: {response.status_code})")
            elif response.status_code == 404:
                print(f"❌ {endpoint} - Not found (Status: {response.status_code})")
            else:
                print(f"⚠️  {endpoint} - Status: {response.status_code}")
                
        except Exception as e:
            print(f"❌ {endpoint} - Error: {e}")
    
    print(f"\n📋 Working endpoints: {working_endpoints}")
    return working_endpoints


def main():
    """Main test function"""
    print("🚀 Starting Qogita API Integration Tests")
    
    # Test authentication
    auth_success = test_qogita_authentication()
    
    if not auth_success:
        print("\n❌ Cannot proceed with further tests due to authentication failure")
        return
    
    # Create authenticated API instance
    config = load_config()
    qogita_settings = config.get('qogita_settings', {})
    api = QogitaAPI(qogita_settings['email'], qogita_settings['password'])
    api.authenticate()
    
    # Discover API endpoints
    discover_api_endpoints(api)
    
    # Test product search with common brands
    test_brands = [
        "Nike",
        "Apple", 
        "Samsung",
        "Sony",
        "Logitech"
    ]
    
    test_product_search(api, test_brands)
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
