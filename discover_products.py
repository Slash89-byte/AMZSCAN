"""
Targeted Qogita API brand search and product discovery.
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
    
    return None


def test_brand_search(api: QogitaAPI, brand_name: str):
    """Test brand search with different parameters"""
    print(f"\n🔍 Searching for brand: '{brand_name}'")
    print("-" * 40)
    
    search_params = [
        {"search": brand_name},
        {"q": brand_name},
        {"query": brand_name},
        {"name": brand_name}
    ]
    
    best_result = None
    best_count = 0
    
    for params in search_params:
        try:
            response = api.session.get(f"{api.base_url}/brands/", params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                count = data.get('count', 0)
                results = data.get('results', [])
                
                print(f"📊 Params {params}: {count} brands found, {len(results)} in current page")
                
                if results and count > best_count:
                    best_result = data
                    best_count = count
                
                # Show first few results
                for i, brand in enumerate(results[:3]):
                    brand_name_found = brand.get('name', 'N/A')
                    brand_id = brand.get('id', 'N/A')
                    print(f"   {i+1}. {brand_name_found} (ID: {brand_id})")
                    
            else:
                print(f"❌ Params {params}: Status {response.status_code}")
                
        except Exception as e:
            print(f"❌ Params {params}: Error {e}")
    
    return best_result


def explore_brand_products(api: QogitaAPI, brand_id: str, brand_name: str):
    """Try to find products for a specific brand"""
    print(f"\n🔍 Looking for products from brand ID: {brand_id} ({brand_name})")
    print("-" * 50)
    
    # Try different endpoint patterns with brand ID
    endpoints_to_try = [
        f"/brands/{brand_id}/",
        f"/brands/{brand_id}/products/",
        f"/products/?brand={brand_id}",
        f"/products/?brand_id={brand_id}",
        f"/catalog/?brand={brand_id}",
        f"/items/?brand={brand_id}",
        f"/search/?brand={brand_id}",
        f"/search/products/?brand={brand_id}",
    ]
    
    for endpoint in endpoints_to_try:
        try:
            print(f"🔍 Trying: {endpoint}")
            response = api.session.get(f"{api.base_url}{endpoint}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Success! Response type: {type(data)}")
                
                if isinstance(data, dict):
                    if 'results' in data:
                        results = data['results']
                        print(f"   📦 Found {len(results)} items in results")
                        
                        # Check if these look like products
                        if results:
                            first_item = results[0]
                            print(f"   📋 First item keys: {list(first_item.keys())}")
                            
                            # Look for product-like fields
                            product_fields = ['name', 'title', 'price', 'ean', 'gtin', 'description']
                            found_fields = [field for field in product_fields if field in first_item]
                            print(f"   🔍 Product-like fields found: {found_fields}")
                            
                            return data
                    elif 'count' in data:
                        print(f"   📊 Paginated response with {data.get('count')} total items")
                        return data
                    else:
                        print(f"   📋 Object keys: {list(data.keys())}")
                        
                elif isinstance(data, list):
                    print(f"   📦 Found {len(data)} items in list")
                    if data:
                        first_item = data[0]
                        print(f"   📋 First item keys: {list(first_item.keys())}")
                        
                        # Look for product-like fields
                        product_fields = ['name', 'title', 'price', 'ean', 'gtin', 'description']
                        found_fields = [field for field in product_fields if field in first_item]
                        print(f"   🔍 Product-like fields found: {found_fields}")
                        
                        return data
                
            elif response.status_code == 404:
                print(f"   ❌ Not found")
            else:
                print(f"   ⚠️  Status: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    return None


def test_general_product_search(api: QogitaAPI):
    """Try to find a general product search endpoint"""
    print(f"\n🔍 Looking for general product search...")
    print("-" * 40)
    
    # Try different search endpoints with product-related terms
    search_tests = [
        ("/search/", {"q": "phone"}),
        ("/search/", {"search": "phone"}),
        ("/search/", {"query": "phone"}),
        ("/products/", {}),
        ("/product/", {}),
        ("/catalog/", {}),
        ("/items/", {}),
        ("/inventory/", {}),
    ]
    
    for endpoint, params in search_tests:
        try:
            print(f"🔍 Trying: {endpoint} with {params}")
            response = api.session.get(f"{api.base_url}{endpoint}", params=params)
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Success! Response type: {type(data)}")
                
                if isinstance(data, dict):
                    if 'results' in data:
                        results = data['results']
                        print(f"   📦 Found {len(results)} items")
                        if results:
                            print(f"   📋 First item keys: {list(results[0].keys())}")
                            return endpoint, data
                    else:
                        print(f"   📋 Object keys: {list(data.keys())}")
                        
                elif isinstance(data, list):
                    print(f"   📦 Found {len(data)} items")
                    if data:
                        print(f"   📋 First item keys: {list(data[0].keys())}")
                        return endpoint, data
                
            elif response.status_code == 404:
                print(f"   ❌ Not found")
            else:
                print(f"   ⚠️  Status: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    return None, None


def main():
    """Main function to discover product search patterns"""
    print("🔍 Qogita API Product Discovery")
    
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
    
    # Test brand search
    test_brands = ["Nike", "Apple", "Samsung"]
    
    for brand in test_brands:
        brand_data = test_brand_search(api, brand)
        
        if brand_data and brand_data.get('results'):
            # Try to find products for the first brand found
            first_brand = brand_data['results'][0]
            brand_id = first_brand.get('id')
            brand_name = first_brand.get('name')
            
            if brand_id:
                products = explore_brand_products(api, brand_id, brand_name)
                if products:
                    print(f"   ✅ Found products for {brand_name}!")
                    break
    
    # Try general product search
    endpoint, data = test_general_product_search(api)
    if endpoint and data:
        print(f"   ✅ Found general product endpoint: {endpoint}")
    
    print("\n" + "=" * 60)
    print("DISCOVERY COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
