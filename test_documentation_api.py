"""
Test Qogita API based on official documentation structure.
Testing the correct endpoints: /variants/, /variants/{search}/, and brand-based searching.
"""

import sys
import os
import json

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.qogita_api import QogitaAPI

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


def test_variants_endpoint(api: QogitaAPI):
    """Test the variants endpoints based on documentation"""
    print("🔍 Testing Variants Endpoints (From Documentation)")
    print("=" * 55)
    
    # Test if there's a general /variants/ endpoint
    try:
        print("📦 Testing general /variants/ endpoint...")
        response = api.session.get(f"{api.base_url}/variants/")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ /variants/ works! Response type: {type(data)}")
            
            if isinstance(data, dict):
                print(f"📊 Response structure:")
                for key, value in data.items():
                    if isinstance(value, list):
                        print(f"   {key}: List with {len(value)} items")
                        if value and isinstance(value[0], dict):
                            print(f"      First item keys: {list(value[0].keys())}")
                    else:
                        print(f"   {key}: {type(value).__name__} = {value}")
                        
                # Check if we can find products
                results = data.get('results', [])
                if results:
                    first_variant = results[0]
                    print(f"\n🎯 First variant details:")
                    for key, value in first_variant.items():
                        print(f"   {key}: {value}")
                    
                    return data
                    
        elif response.status_code == 404:
            print("❌ /variants/ endpoint not found")
        else:
            print(f"⚠️ /variants/ returned status: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing /variants/: {e}")
    
    return None


def test_variants_with_params(api: QogitaAPI):
    """Test variants endpoint with different query parameters"""
    print("\n🔍 Testing /variants/ with Query Parameters")
    print("=" * 45)
    
    # Test different parameter combinations
    test_params = [
        {"page": 1, "page_size": 10},
        {"search": "phone"},
        {"q": "phone"},
        {"brand": "Apple"},
        {"category": "Electronics"},
        {},  # No parameters
    ]
    
    for params in test_params:
        try:
            print(f"📋 Testing params: {params}")
            response = api.session.get(f"{api.base_url}/variants/", params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                if isinstance(data, dict) and 'results' in data:
                    results = data['results']
                    count = data.get('count', len(results))
                    print(f"   ✅ Found {len(results)} variants (total: {count})")
                    
                    if results:
                        first_variant = results[0]
                        # Show key product information
                        product_info = {
                            'name': first_variant.get('name', 'N/A'),
                            'brand': first_variant.get('brand', 'N/A'),
                            'ean': first_variant.get('ean', first_variant.get('gtin', 'N/A')),
                            'price': first_variant.get('price', first_variant.get('cost', 'N/A')),
                        }
                        print(f"   📦 Sample: {product_info}")
                        
                        return data
                elif isinstance(data, list):
                    print(f"   ✅ Found {len(data)} variants")
                    if data:
                        first_variant = data[0]
                        print(f"   📦 First variant keys: {list(first_variant.keys())}")
                        return data
                else:
                    print(f"   📊 Response: {type(data)} with keys: {list(data.keys()) if isinstance(data, dict) else 'N/A'}")
                    
            elif response.status_code == 404:
                print(f"   ❌ Not found")
            else:
                print(f"   ⚠️ Status: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    return None


def test_specific_variant_search(api: QogitaAPI):
    """Test the /variants/{search}/ endpoint with different search terms"""
    print("\n🔍 Testing /variants/{search}/ Endpoint")
    print("=" * 40)
    
    # Get some brand QIDs first
    brands_response = api.session.get(f"{api.base_url}/brands/", params={"page": 1, "page_size": 5})
    
    if brands_response.status_code == 200:
        brands_data = brands_response.json()
        brands = brands_data.get('results', [])
        
        print(f"📋 Testing with brand QIDs from first {len(brands)} brands:")
        
        for brand in brands:
            brand_name = brand.get('name')
            brand_qid = brand.get('qid')
            variant_count = brand.get('variantCount', 0)
            
            if variant_count > 0:
                print(f"\n🔍 Testing brand: {brand_name} (QID: {brand_qid}, {variant_count} variants)")
                
                # Try searching for variants using brand QID
                try:
                    response = api.session.get(f"{api.base_url}/variants/{brand_qid}/")
                    
                    if response.status_code == 200:
                        data = response.json()
                        print(f"   ✅ Found variant data! Type: {type(data)}")
                        
                        if isinstance(data, dict):
                            print(f"   📋 Variant keys: {list(data.keys())}")
                            # Show key product information
                            product_info = {
                                'name': data.get('name', 'N/A'),
                                'brand': data.get('brand', 'N/A'),
                                'ean': data.get('ean', data.get('gtin', 'N/A')),
                                'price': data.get('price', data.get('cost', 'N/A')),
                            }
                            print(f"   📦 Product info: {product_info}")
                            return data
                        
                    elif response.status_code == 404:
                        print(f"   ❌ No variant found for brand QID")
                    else:
                        print(f"   ⚠️ Status: {response.status_code}")
                        
                except Exception as e:
                    print(f"   ❌ Error: {e}")
    
    # Also try some common search terms
    search_terms = ["phone", "samsung", "apple", "electronics"]
    
    print(f"\n🔍 Testing with common search terms:")
    for term in search_terms:
        try:
            response = api.session.get(f"{api.base_url}/variants/{term}/")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ '{term}' found variant! Type: {type(data)}")
                
                if isinstance(data, dict):
                    product_info = {
                        'name': data.get('name', 'N/A'),
                        'brand': data.get('brand', 'N/A'),
                        'ean': data.get('ean', data.get('gtin', 'N/A')),
                    }
                    print(f"   📦 Product: {product_info}")
                    return data
                    
            elif response.status_code == 404:
                print(f"❌ '{term}' - Not found")
            else:
                print(f"⚠️ '{term}' - Status: {response.status_code}")
                
        except Exception as e:
            print(f"❌ '{term}' - Error: {e}")
    
    return None


def test_advanced_brand_search(api: QogitaAPI):
    """Test advanced brand search and filtering"""
    print("\n🔍 Testing Advanced Brand Search")
    print("=" * 35)
    
    # Test brand search with specific brand names
    brand_searches = ["Nike", "Apple", "Samsung", "Sony"]
    
    for brand_name in brand_searches:
        print(f"\n🔍 Searching for exact brand: '{brand_name}'")
        
        try:
            # Try different search approaches
            search_params = [
                {"search": brand_name},
                {"name": brand_name},
                {"name__icontains": brand_name},
                {"name__exact": brand_name},
            ]
            
            for params in search_params:
                response = api.session.get(f"{api.base_url}/brands/", params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get('results', [])
                    
                    # Look for exact brand matches
                    exact_matches = [b for b in results if b.get('name', '').lower() == brand_name.lower()]
                    
                    if exact_matches:
                        print(f"   ✅ Found exact match with params {params}")
                        brand = exact_matches[0]
                        brand_qid = brand.get('qid')
                        variant_count = brand.get('variantCount', 0)
                        
                        print(f"   📦 Brand: {brand.get('name')} (QID: {brand_qid}, {variant_count} variants)")
                        
                        if variant_count > 0:
                            # This brand has variants - we'll use this QID later
                            return brand
                        
        except Exception as e:
            print(f"   ❌ Error searching for '{brand_name}': {e}")
    
    return None


def main():
    """Main test function based on official documentation"""
    print("🚀 Qogita API Testing - Based on Official Documentation")
    print("=" * 60)
    
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
    
    # Test variants endpoints
    variants_data = test_variants_endpoint(api)
    
    if not variants_data:
        variants_data = test_variants_with_params(api)
    
    if not variants_data:
        variants_data = test_specific_variant_search(api)
    
    # Test advanced brand search
    exact_brand = test_advanced_brand_search(api)
    
    print("\n" + "=" * 60)
    print("DOCUMENTATION-BASED TESTING COMPLETE")
    print("=" * 60)
    
    if variants_data:
        print("🎉 SUCCESS: Found working variant endpoint!")
        print("🔧 Ready to implement brand-based product discovery")
    elif exact_brand:
        print("🎯 SUCCESS: Found exact brand matching!")
        print("🔧 Can proceed with brand-based workflow")
    else:
        print("🤔 Need to explore further API patterns")


if __name__ == "__main__":
    main()
