"""
Final attempt to discover Qogita product endpoints using all available information.
"""

import sys
import os
import json

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.qogita_api import QogitaAPI, QogitaAPIError

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
        except:
            continue
    return None


def test_all_possible_endpoints(api: QogitaAPI):
    """Test every possible endpoint pattern we can think of"""
    print("🔍 Testing All Possible Endpoint Patterns")
    print("=" * 50)
    
    # Get a brand with many variants for testing
    brand_qid = "85ebc4da-9f49-47b7-b766-9d34b598a66c"  # 3ina (253 variants)
    brand_slug = "3ina"
    
    print(f"Testing with brand: 3ina (QID: {brand_qid})")
    
    # Every possible endpoint pattern
    all_endpoints = [
        # Basic endpoints
        "/variants/",
        "/products/",
        "/catalog/",
        "/items/",
        "/inventory/",
        "/listings/",
        "/offers/",
        "/goods/",
        "/merchandise/",
        
        # API versioned endpoints
        "/api/variants/",
        "/api/products/",
        "/api/catalog/",
        "/api/v1/variants/",
        "/api/v1/products/",
        "/api/v2/variants/",
        "/api/v2/products/",
        "/v1/variants/",
        "/v1/products/",
        "/v2/variants/",
        "/v2/products/",
        
        # Brand-specific patterns
        f"/brands/{brand_qid}/variants/",
        f"/brands/{brand_qid}/products/",
        f"/brands/{brand_qid}/catalog/",
        f"/brands/{brand_qid}/items/",
        f"/brands/{brand_slug}/variants/",
        f"/brands/{brand_slug}/products/",
        
        # Search patterns with parameters
        "/search/",
        "/find/",
        "/query/",
        
        # Alternative structures
        "/brand-variants/",
        "/brand-products/",
        "/product-catalog/",
        "/variant-catalog/",
        
        # Possible nested structures
        "/catalog/brands/",
        "/catalog/variants/",
        "/catalog/products/",
        "/inventory/brands/",
        "/inventory/variants/",
        "/listings/variants/",
        "/offers/variants/",
    ]
    
    working_endpoints = []
    
    for endpoint in all_endpoints:
        try:
            response = api.session.get(f"{api.base_url}{endpoint}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"✅ {endpoint} - SUCCESS!")
                    print(f"   Response type: {type(data)}")
                    
                    if isinstance(data, dict):
                        if 'results' in data:
                            results = data['results']
                            print(f"   📦 Found {len(results)} items")
                            
                            if results:
                                first_item = results[0]
                                keys = list(first_item.keys())
                                print(f"   🔍 First item keys: {keys}")
                                
                                # Check for product-like fields
                                product_fields = ['ean', 'gtin', 'barcode', 'sku', 'price', 'cost', 'wholesale_price', 'name', 'title']
                                found_fields = [field for field in product_fields if field in first_item]
                                
                                if found_fields:
                                    print(f"   🎯 PRODUCT FIELDS FOUND: {found_fields}")
                                    working_endpoints.append((endpoint, data))
                                    
                                    # Show sample data
                                    print(f"   📋 Sample product data:")
                                    for key, value in list(first_item.items())[:8]:
                                        print(f"      {key}: {value}")
                        else:
                            print(f"   📋 Object keys: {list(data.keys())}")
                    
                    elif isinstance(data, list) and data:
                        print(f"   📦 Found {len(data)} items in list")
                        first_item = data[0]
                        keys = list(first_item.keys())
                        print(f"   🔍 First item keys: {keys}")
                        
                        # Check for product fields
                        product_fields = ['ean', 'gtin', 'barcode', 'sku', 'price', 'cost', 'wholesale_price']
                        found_fields = [field for field in product_fields if field in first_item]
                        
                        if found_fields:
                            print(f"   🎯 PRODUCT FIELDS FOUND: {found_fields}")
                            working_endpoints.append((endpoint, data))
                    
                except json.JSONDecodeError:
                    print(f"✅ {endpoint} - Non-JSON response")
                    
            elif response.status_code == 401:
                print(f"🔐 {endpoint} - Authentication required")
            elif response.status_code == 403:
                print(f"🚫 {endpoint} - Forbidden (may need permissions)")
            elif response.status_code != 404:
                print(f"⚠️  {endpoint} - Status: {response.status_code}")
                
        except Exception as e:
            continue  # Skip errors to avoid spam
    
    return working_endpoints


def test_parameter_combinations(api: QogitaAPI):
    """Test parameter combinations on working endpoints"""
    print(f"\n🔍 Testing Parameter Combinations")
    print("=" * 40)
    
    base_endpoints = ["/brands/", "/categories/"]
    brand_qid = "85ebc4da-9f49-47b7-b766-9d34b598a66c"  # 3ina
    
    parameter_combinations = [
        {"include": "variants"},
        {"include": "products"},
        {"expand": "variants"},
        {"expand": "products"},
        {"with": "variants"},
        {"with": "products"},
        {"embed": "variants"},
        {"embed": "products"},
        {"fields": "variants"},
        {"related": "variants"},
        {"nested": "true"},
        {"full": "true"},
        {"detailed": "true"},
        {"complete": "true"},
    ]
    
    for endpoint in base_endpoints:
        for params in parameter_combinations:
            try:
                print(f"🔍 {endpoint} with {params}")
                response = api.session.get(f"{api.base_url}{endpoint}", params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Check if we get different/more data
                    if isinstance(data, dict) and 'results' in data:
                        results = data['results']
                        if results:
                            first_item = results[0]
                            keys = set(first_item.keys())
                            
                            # Look for new keys that might indicate embedded data
                            new_keys = keys - {'name', 'slug', 'description', 'variantCount', 'qid'}
                            if new_keys:
                                print(f"   ✅ New keys found: {new_keys}")
                                
                                # Check if any new key contains product data
                                for key in new_keys:
                                    value = first_item[key]
                                    if isinstance(value, (list, dict)):
                                        print(f"      🔍 {key}: {type(value)} - might contain product data")
                                        if isinstance(value, list) and value:
                                            print(f"         First item in {key}: {type(value[0])}")
                                        return endpoint, params, data
                
            except Exception:
                continue


def test_known_working_patterns(api: QogitaAPI):
    """Test patterns based on documentation hints"""
    print(f"\n🔍 Testing Documentation-Based Patterns")
    print("=" * 45)
    
    # From the documentation, we know variants can be searched by QID/GTIN
    # Let's try to find some actual variant QIDs or GTINs
    
    # Try some test searches that might reveal variant structure
    test_searches = [
        "/search/?q=shampoo",
        "/search/?q=cream",
        "/search/?q=lotion",
        "/search/?query=makeup",
        "/find/?q=cosmetics",
        "/query/?search=beauty",
    ]
    
    for search in test_searches:
        try:
            response = api.session.get(f"{api.base_url}{search}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ {search} - Found data!")
                
                if isinstance(data, dict) and 'results' in data:
                    results = data['results']
                    print(f"   📦 {len(results)} search results")
                    
                    if results:
                        first_result = results[0]
                        print(f"   🔍 Result keys: {list(first_result.keys())}")
                        
                        # Look for variant or product identifiers
                        for key, value in first_result.items():
                            if 'qid' in key.lower() or 'id' in key.lower():
                                print(f"      ID field {key}: {value}")
                                
                                # Try using this as a variant search
                                try:
                                    variant_response = api.session.get(f"{api.base_url}/variants/{value}/")
                                    if variant_response.status_code == 200:
                                        variant_data = variant_response.json()
                                        print(f"      🎯 FOUND VARIANT DATA using {key}!")
                                        return f"/variants/{value}/", variant_data
                                except:
                                    continue
                
        except Exception:
            continue
    
    return None, None


def main():
    """Final comprehensive test"""
    config = load_config()
    if not config:
        print("❌ Cannot load configuration")
        return
    
    qogita_settings = config.get('qogita_settings', {})
    api = QogitaAPI(qogita_settings['email'], qogita_settings['password'])
    
    try:
        api.authenticate()
        print("✅ Authentication successful\n")
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return
    
    print("🔍 FINAL COMPREHENSIVE QOGITA API EXPLORATION")
    print("=" * 60)
    
    # Test 1: All possible endpoints
    working_endpoints = test_all_possible_endpoints(api)
    
    if working_endpoints:
        print(f"\n🎉 BREAKTHROUGH! Found {len(working_endpoints)} working product endpoints!")
        for endpoint, data in working_endpoints:
            print(f"   ✅ {endpoint}")
        return
    
    # Test 2: Parameter combinations
    result = test_parameter_combinations(api)
    if result:
        endpoint, params, data = result
        print(f"\n🎉 BREAKTHROUGH! Parameter combination worked: {endpoint} with {params}")
        return
    
    # Test 3: Documentation patterns
    result = test_known_working_patterns(api)
    if result:
        endpoint, data = result
        print(f"\n🎉 BREAKTHROUGH! Found variant endpoint: {endpoint}")
        return
    
    print(f"\n🤔 CONCLUSION:")
    print(f"   • Authentication: ✅ Working")
    print(f"   • Brand access: ✅ Working (/brands/)")
    print(f"   • Category access: ✅ Working (/categories/)")
    print(f"   • Product access: ❌ Not discoverable")
    print(f"\nPossible reasons:")
    print(f"   1. API requires additional permissions/scopes")
    print(f"   2. Product access is restricted to certain account types")
    print(f"   3. Different authentication method needed for product data")
    print(f"   4. Products only accessible through specific variant IDs/GTINs")


if __name__ == "__main__":
    main()
