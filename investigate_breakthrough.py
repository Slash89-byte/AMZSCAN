"""
Investigate the breakthrough: /categories/ with include=variants parameter.
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


def investigate_categories_breakthrough(api: QogitaAPI):
    """Deep dive into the categories breakthrough"""
    print("🎯 Investigating Categories Breakthrough")
    print("=" * 50)
    
    # Test the working parameter combination
    response = api.session.get(f"{api.base_url}/categories/", params={"include": "variants"})
    
    if response.status_code == 200:
        data = response.json()
        
        print(f"✅ Successfully retrieved categories with variants")
        print(f"📊 Response structure:")
        print(f"   Type: {type(data)}")
        print(f"   Keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
        
        if isinstance(data, dict) and 'results' in data:
            results = data['results']
            print(f"   📦 Found {len(results)} categories")
            
            # Analyze categories with variants
            categories_with_variants = []
            for category in results:
                variant_count = category.get('variantCount', 0)
                if variant_count > 0:
                    categories_with_variants.append(category)
            
            print(f"   🔍 Categories with variants: {len(categories_with_variants)}")
            
            # Show detailed analysis of first few categories
            for i, category in enumerate(categories_with_variants[:5]):
                print(f"\n📂 Category {i+1}: {category.get('name', 'Unknown')}")
                print(f"   Variant Count: {category.get('variantCount', 0)}")
                print(f"   QID: {category.get('qid')}")
                
                # Show all fields
                print(f"   📋 All fields:")
                for key, value in category.items():
                    if key == 'path' and isinstance(value, list):
                        print(f"      {key}: {value} (list with {len(value)} items)")
                    elif isinstance(value, str) and len(value) > 50:
                        print(f"      {key}: {value[:50]}... (truncated)")
                    else:
                        print(f"      {key}: {value}")
                
                # Try to get variants for this category
                category_qid = category.get('qid')
                if category_qid:
                    print(f"\n   🔍 Trying to get variants for category {category_qid}:")
                    
                    variant_endpoints = [
                        f"/categories/{category_qid}/variants/",
                        f"/categories/{category_qid}/products/",
                        f"/variants/?category={category_qid}",
                        f"/variants/?category_qid={category_qid}",
                        f"/products/?category={category_qid}",
                        f"/offers/?category={category_qid}",
                    ]
                    
                    for endpoint in variant_endpoints:
                        try:
                            variant_response = api.session.get(f"{api.base_url}{endpoint}")
                            
                            if variant_response.status_code == 200:
                                variant_data = variant_response.json()
                                
                                print(f"      ✅ {endpoint} - SUCCESS!")
                                
                                if isinstance(variant_data, dict) and 'results' in variant_data:
                                    variant_results = variant_data['results']
                                    print(f"         📦 Found {len(variant_results)} variants!")
                                    
                                    if variant_results:
                                        first_variant = variant_results[0]
                                        print(f"         🔍 First variant keys: {list(first_variant.keys())}")
                                        
                                        # Check for product fields
                                        product_fields = ['ean', 'gtin', 'barcode', 'price', 'cost', 'wholesale_price', 'name', 'title']
                                        found_fields = [field for field in product_fields if field in first_variant]
                                        
                                        if found_fields:
                                            print(f"         🎯 PRODUCT FIELDS: {found_fields}")
                                            print(f"         📋 Sample variant data:")
                                            for field in found_fields:
                                                print(f"            {field}: {first_variant[field]}")
                                            
                                            return endpoint, variant_data  # SUCCESS!
                                
                                elif isinstance(variant_data, list) and variant_data:
                                    print(f"         📦 Found {len(variant_data)} variants in list!")
                                    first_variant = variant_data[0]
                                    print(f"         🔍 First variant keys: {list(first_variant.keys())}")
                                    
                                    product_fields = ['ean', 'gtin', 'barcode', 'price', 'cost', 'wholesale_price']
                                    found_fields = [field for field in product_fields if field in first_variant]
                                    
                                    if found_fields:
                                        print(f"         🎯 PRODUCT FIELDS: {found_fields}")
                                        return endpoint, variant_data
                            
                            elif variant_response.status_code != 404:
                                print(f"      ⚠️  {endpoint} - Status: {variant_response.status_code}")
                        
                        except Exception as e:
                            continue
    
    return None, None


def test_offers_endpoint(api: QogitaAPI):
    """Investigate the /offers/ endpoint that returned empty results"""
    print(f"\n🔍 Investigating /offers/ Endpoint")
    print("=" * 40)
    
    # Test offers with different parameters
    offer_params = [
        {},
        {"page": 1, "page_size": 50},
        {"include": "variants"},
        {"include": "products"},
        {"expand": "variants"},
        {"category": "beauty"},
        {"category": "cosmetics"},
        {"brand": "3ina"},
        {"active": "true"},
        {"available": "true"},
    ]
    
    for params in offer_params:
        try:
            print(f"🔍 Testing /offers/ with {params}")
            response = api.session.get(f"{api.base_url}/offers/", params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                if isinstance(data, dict) and 'results' in data:
                    results = data['results']
                    count = data.get('count', 0)
                    
                    print(f"   ✅ Success: {len(results)} results, {count} total")
                    
                    if results:
                        first_offer = results[0]
                        print(f"   🔍 First offer keys: {list(first_offer.keys())}")
                        
                        # Look for product-related data in offers
                        product_fields = ['ean', 'gtin', 'barcode', 'price', 'cost', 'wholesale_price', 'variant', 'product']
                        found_fields = [field for field in product_fields if field in first_offer]
                        
                        if found_fields:
                            print(f"   🎯 PRODUCT FIELDS FOUND: {found_fields}")
                            print(f"   📋 Sample offer data:")
                            for field in found_fields:
                                print(f"      {field}: {first_offer[field]}")
                            
                            return "/offers/", data
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    return None, None


def test_more_include_parameters(api: QogitaAPI):
    """Test more include parameters on different endpoints"""
    print(f"\n🔍 Testing More Include Parameters")
    print("=" * 40)
    
    endpoints = ["/brands/", "/categories/", "/offers/"]
    include_params = [
        "variants",
        "products", 
        "items",
        "catalog",
        "inventory",
        "details",
        "pricing",
        "stock",
        "availability",
        "images",
        "specifications",
        "full"
    ]
    
    for endpoint in endpoints:
        for param in include_params:
            try:
                response = api.session.get(f"{api.base_url}{endpoint}", params={"include": param})
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if isinstance(data, dict) and 'results' in data:
                        results = data['results']
                        
                        if results:
                            first_item = results[0]
                            standard_keys = {'name', 'slug', 'description', 'variantCount', 'qid'}
                            all_keys = set(first_item.keys())
                            new_keys = all_keys - standard_keys
                            
                            if new_keys:
                                print(f"✅ {endpoint} + include={param}: New keys {new_keys}")
                                
                                # Check for promising new keys
                                promising_keys = ['variants', 'products', 'items', 'catalog', 'inventory', 'offers']
                                found_promising = [key for key in new_keys if any(p in key.lower() for p in promising_keys)]
                                
                                if found_promising:
                                    print(f"   🎯 PROMISING KEYS: {found_promising}")
                                    
                                    for key in found_promising:
                                        value = first_item[key]
                                        print(f"      {key}: {type(value)} - {value if not isinstance(value, (list, dict)) else f'{type(value)} with {len(value) if hasattr(value, "__len__") else "?"} items'}")
                                        
                                        if isinstance(value, list) and value:
                                            print(f"         First item in {key}: {type(value[0])}")
                                            if isinstance(value[0], dict):
                                                print(f"         Keys in first item: {list(value[0].keys())}")
                                                return endpoint, {"include": param}, data
                
            except Exception:
                continue
    
    return None, None


def main():
    """Main investigation function"""
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
    
    print("🔍 INVESTIGATING QOGITA API BREAKTHROUGH")
    print("=" * 50)
    
    # 1. Deep dive into categories with variants
    result = investigate_categories_breakthrough(api)
    if result:
        endpoint, data = result
        print(f"\n🎉 MAJOR BREAKTHROUGH! Found variants at: {endpoint}")
        return
    
    # 2. Investigate offers endpoint
    result = test_offers_endpoint(api)
    if result:
        endpoint, data = result
        print(f"\n🎉 BREAKTHROUGH! Found product data in offers: {endpoint}")
        return
    
    # 3. Test more include parameters
    result = test_more_include_parameters(api)
    if result:
        endpoint, params, data = result
        print(f"\n🎉 BREAKTHROUGH! Found embedded data: {endpoint} with {params}")
        return
    
    print(f"\n🤔 INVESTIGATION COMPLETE")
    print(f"Found some promising patterns but still need to discover the exact endpoint for product data.")


if __name__ == "__main__":
    main()
