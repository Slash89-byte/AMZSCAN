"""
Test product discovery using brand QIDs and variant information.
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


def test_variant_endpoints(api: QogitaAPI):
    """Test variant-related endpoints using brand QIDs"""
    print("🔍 Testing Variant/Product Endpoints")
    print("=" * 50)
    
    # Get some brands with variants
    response = api.session.get(f"{api.base_url}/brands/", params={"page": 1, "page_size": 10})
    
    if response.status_code == 200:
        data = response.json()
        brands_with_variants = [b for b in data.get('results', []) if b.get('variantCount', 0) > 0]
        
        print(f"Found {len(brands_with_variants)} brands with variants")
        
        for brand in brands_with_variants[:3]:  # Test first 3 brands
            brand_name = brand.get('name')
            brand_qid = brand.get('qid')
            variant_count = brand.get('variantCount')
            
            print(f"\n📦 Testing brand: {brand_name} ({variant_count} variants)")
            print(f"   QID: {brand_qid}")
            
            # Test different variant/product endpoints
            endpoints_to_try = [
                f"/brands/{brand_qid}/",
                f"/brands/{brand_qid}/variants/",
                f"/brands/{brand_qid}/products/",
                f"/variants/?brand={brand_qid}",
                f"/variants/?brand_qid={brand_qid}",
                f"/products/?brand={brand_qid}",
                f"/products/?brand_qid={brand_qid}",
                f"/catalog/?brand={brand_qid}",
                f"/catalog/?brand_qid={brand_qid}",
                f"/items/?brand={brand_qid}",
                f"/items/?brand_qid={brand_qid}",
            ]
            
            for endpoint in endpoints_to_try:
                try:
                    test_response = api.session.get(f"{api.base_url}{endpoint}")
                    
                    if test_response.status_code == 200:
                        test_data = test_response.json()
                        
                        print(f"   ✅ {endpoint}")
                        print(f"      Response type: {type(test_data)}")
                        
                        if isinstance(test_data, dict):
                            if 'results' in test_data:
                                results = test_data['results']
                                print(f"      Found {len(results)} items in results")
                                
                                if results:
                                    first_item = results[0]
                                    print(f"      First item keys: {list(first_item.keys())}")
                                    
                                    # Check for product-like fields
                                    product_fields = ['name', 'title', 'price', 'ean', 'gtin', 'description', 'cost', 'wholesale_price']
                                    found_fields = [field for field in product_fields if field in first_item]
                                    if found_fields:
                                        print(f"      🎯 Product fields found: {found_fields}")
                                        print(f"      Sample values:")
                                        for field in found_fields[:3]:
                                            print(f"         {field}: {first_item[field]}")
                                        
                                        return endpoint, test_data
                            
                            elif 'count' in test_data:
                                print(f"      Paginated response with {test_data.get('count')} items")
                            else:
                                print(f"      Object keys: {list(test_data.keys())}")
                                
                                # Check if this is detailed brand info
                                if 'variants' in test_data or 'products' in test_data:
                                    print(f"      🎯 Contains product/variant data!")
                                    return endpoint, test_data
                        
                        elif isinstance(test_data, list):
                            print(f"      Found {len(test_data)} items in list")
                            if test_data:
                                first_item = test_data[0]
                                print(f"      First item keys: {list(first_item.keys())}")
                                
                                # Check for product-like fields
                                product_fields = ['name', 'title', 'price', 'ean', 'gtin', 'description', 'cost', 'wholesale_price']
                                found_fields = [field for field in product_fields if field in first_item]
                                if found_fields:
                                    print(f"      🎯 Product fields found: {found_fields}")
                                    return endpoint, test_data
                    
                    elif test_response.status_code == 404:
                        print(f"   ❌ {endpoint} - Not found")
                    else:
                        print(f"   ⚠️  {endpoint} - Status: {test_response.status_code}")
                        
                except Exception as e:
                    print(f"   ❌ {endpoint} - Error: {e}")
    
    return None, None


def test_other_endpoints(api: QogitaAPI):
    """Test other possible endpoints"""
    print("\n🔍 Testing Other Possible Endpoints")
    print("=" * 40)
    
    other_endpoints = [
        "/variants/",
        "/variant/",
        "/listings/",
        "/listing/", 
        "/inventory/",
        "/catalog/",
        "/search/",
    ]
    
    for endpoint in other_endpoints:
        try:
            response = api.session.get(f"{api.base_url}{endpoint}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ {endpoint} - Status: 200")
                
                if isinstance(data, dict):
                    if 'results' in data:
                        results = data['results']
                        print(f"   📦 Found {len(results)} items")
                        if results:
                            first_item = results[0]
                            print(f"   📋 First item keys: {list(first_item.keys())}")
                            
                            # Check for product-like fields
                            product_fields = ['name', 'title', 'price', 'ean', 'gtin', 'description', 'cost', 'wholesale_price']
                            found_fields = [field for field in product_fields if field in first_item]
                            if found_fields:
                                print(f"   🎯 Product fields found: {found_fields}")
                                return endpoint, data
                    else:
                        print(f"   📋 Object keys: {list(data.keys())}")
                        
                elif isinstance(data, list):
                    print(f"   📦 Found {len(data)} items")
                    if data:
                        print(f"   📋 First item keys: {list(data[0].keys())}")
                        
                        # Check for product-like fields
                        product_fields = ['name', 'title', 'price', 'ean', 'gtin', 'description', 'cost', 'wholesale_price']
                        found_fields = [field for field in product_fields if field in data[0]]
                        if found_fields:
                            print(f"   🎯 Product fields found: {found_fields}")
                            return endpoint, data
            
            elif response.status_code == 404:
                print(f"❌ {endpoint} - Not found")
            else:
                print(f"⚠️  {endpoint} - Status: {response.status_code}")
                
        except Exception as e:
            print(f"❌ {endpoint} - Error: {e}")
    
    return None, None


def main():
    """Main discovery function"""
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
    
    # Test variant endpoints
    endpoint, data = test_variant_endpoints(api)
    
    if endpoint and data:
        print(f"\n🎉 SUCCESS! Found product endpoint: {endpoint}")
        return
    
    # Test other endpoints
    endpoint, data = test_other_endpoints(api)
    
    if endpoint and data:
        print(f"\n🎉 SUCCESS! Found product endpoint: {endpoint}")
    else:
        print(f"\n🤔 Still exploring... May need to check documentation or try different approach")


if __name__ == "__main__":
    main()
