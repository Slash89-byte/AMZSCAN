"""
Advanced Qogita API endpoint discovery and testing.
This script explores the working endpoints to understand the API structure.
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
    possible_paths = [
        'config.json',
        os.path.join(os.path.dirname(__file__), 'config.json'),
        os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
    ]
    
    for config_path in possible_paths:
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    return json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing config.json: {e}")
            return None
    
    logger.error("config.json not found in any of the expected locations")
    return None


def explore_brands_endpoint(api: QogitaAPI):
    """Explore the /brands/ endpoint"""
    print("\n" + "=" * 60)
    print("EXPLORING /brands/ ENDPOINT")
    print("=" * 60)
    
    try:
        response = api.session.get(f"{api.base_url}/brands/")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Successfully retrieved brands data")
            print(f"📊 Response type: {type(data)}")
            
            if isinstance(data, list):
                print(f"📋 Found {len(data)} brands")
                if data:
                    print("🔍 First few brands:")
                    for i, brand in enumerate(data[:5]):
                        if isinstance(brand, dict):
                            brand_name = brand.get('name', brand.get('brand', str(brand)))
                            brand_id = brand.get('id', brand.get('brandId', 'N/A'))
                            print(f"   {i+1}. {brand_name} (ID: {brand_id})")
                        else:
                            print(f"   {i+1}. {brand}")
            elif isinstance(data, dict):
                print("📋 Response structure:")
                for key, value in data.items():
                    if isinstance(value, list):
                        print(f"   {key}: List with {len(value)} items")
                    else:
                        print(f"   {key}: {type(value).__name__}")
            
            return data
        else:
            print(f"❌ Failed to retrieve brands: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error exploring brands endpoint: {e}")
        return None


def explore_categories_endpoint(api: QogitaAPI):
    """Explore the /categories/ endpoint"""
    print("\n" + "=" * 60)
    print("EXPLORING /categories/ ENDPOINT")
    print("=" * 60)
    
    try:
        response = api.session.get(f"{api.base_url}/categories/")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Successfully retrieved categories data")
            print(f"📊 Response type: {type(data)}")
            
            if isinstance(data, list):
                print(f"📋 Found {len(data)} categories")
                if data:
                    print("🔍 First few categories:")
                    for i, category in enumerate(data[:5]):
                        if isinstance(category, dict):
                            cat_name = category.get('name', category.get('category', str(category)))
                            cat_id = category.get('id', category.get('categoryId', 'N/A'))
                            print(f"   {i+1}. {cat_name} (ID: {cat_id})")
                        else:
                            print(f"   {i+1}. {category}")
            elif isinstance(data, dict):
                print("📋 Response structure:")
                for key, value in data.items():
                    if isinstance(value, list):
                        print(f"   {key}: List with {len(value)} items")
                    else:
                        print(f"   {key}: {type(value).__name__}")
            
            return data
        else:
            print(f"❌ Failed to retrieve categories: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error exploring categories endpoint: {e}")
        return None


def test_nested_endpoints(api: QogitaAPI):
    """Test common nested endpoint patterns"""
    print("\n" + "=" * 60)
    print("TESTING NESTED ENDPOINTS")
    print("=" * 60)
    
    nested_endpoints = [
        "/brands/products/",
        "/categories/products/",
        "/products/",
        "/product/",
        "/item/", 
        "/items/",
        "/inventory/",
        "/catalog/",
        "/v1/products/",
        "/v2/products/",
        "/api/v1/products/",
        "/api/v2/products/"
    ]
    
    working_endpoints = []
    
    for endpoint in nested_endpoints:
        try:
            response = api.session.get(f"{api.base_url}{endpoint}")
            
            if response.status_code == 200:
                print(f"✅ {endpoint} - Status: {response.status_code}")
                working_endpoints.append(endpoint)
                
                # Try to peek at the response
                try:
                    data = response.json()
                    if isinstance(data, list):
                        print(f"   📋 Returns list with {len(data)} items")
                    elif isinstance(data, dict):
                        print(f"   📋 Returns object with keys: {list(data.keys())[:3]}...")
                except:
                    print(f"   📋 Returns non-JSON data")
                    
            elif response.status_code == 401:
                print(f"🔐 {endpoint} - Authentication required")
            elif response.status_code == 404:
                print(f"❌ {endpoint} - Not found")
            else:
                print(f"⚠️  {endpoint} - Status: {response.status_code}")
                
        except Exception as e:
            print(f"❌ {endpoint} - Error: {e}")
    
    return working_endpoints


def test_search_patterns(api: QogitaAPI):
    """Test different search patterns"""
    print("\n" + "=" * 60)
    print("TESTING SEARCH PATTERNS")
    print("=" * 60)
    
    # Test query parameters on working endpoints
    test_patterns = [
        ("/brands/", {"search": "Nike"}),
        ("/brands/", {"q": "Nike"}),
        ("/brands/", {"query": "Nike"}),
        ("/brands/", {"name": "Nike"}),
        ("/categories/", {"search": "Electronics"}),
        ("/categories/", {"q": "Electronics"}),
    ]
    
    for endpoint, params in test_patterns:
        try:
            print(f"🔍 Testing {endpoint} with params: {params}")
            response = api.session.get(f"{api.base_url}{endpoint}", params=params)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    print(f"   ✅ Success: {len(data)} results")
                elif isinstance(data, dict):
                    print(f"   ✅ Success: Object response")
                else:
                    print(f"   ✅ Success: {type(data)} response")
            else:
                print(f"   ❌ Status: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")


def main():
    """Main exploration function"""
    print("🔍 Advanced Qogita API Exploration")
    
    # Load config and authenticate
    config = load_config()
    if not config:
        print("❌ Cannot load configuration")
        return
    
    qogita_settings = config.get('qogita_settings', {})
    api = QogitaAPI(qogita_settings['email'], qogita_settings['password'])
    
    try:
        api.authenticate()
        print("✅ Authentication successful")
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return
    
    # Explore working endpoints
    brands_data = explore_brands_endpoint(api)
    categories_data = explore_categories_endpoint(api)
    
    # Test nested endpoints
    working_endpoints = test_nested_endpoints(api)
    
    # Test search patterns
    test_search_patterns(api)
    
    print("\n" + "=" * 60)
    print("EXPLORATION COMPLETE")
    print("=" * 60)
    print(f"🔍 Working endpoints discovered: {working_endpoints}")


if __name__ == "__main__":
    main()
