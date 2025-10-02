"""
Deep dive into Qogita API response structure analysis.
"""

import sys
import os
import json
import logging

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
        except json.JSONDecodeError as e:
            return None
    return None


def analyze_response_structure(api: QogitaAPI):
    """Analyze the actual response structure"""
    print("🔍 Deep Analysis of API Response Structure")
    print("=" * 60)
    
    # Get the raw brands response
    try:
        response = api.session.get(f"{api.base_url}/brands/")
        if response.status_code == 200:
            data = response.json()
            
            print("📊 Full Response Structure:")
            print(f"Type: {type(data)}")
            print(f"Keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
            
            if isinstance(data, dict):
                for key, value in data.items():
                    print(f"\n🔑 {key}:")
                    print(f"   Type: {type(value)}")
                    
                    if key == 'results' and isinstance(value, list) and value:
                        print(f"   Length: {len(value)}")
                        print(f"   First item type: {type(value[0])}")
                        
                        if isinstance(value[0], dict):
                            print(f"   First item keys: {list(value[0].keys())}")
                            print(f"   First item values sample:")
                            
                            first_item = value[0]
                            for item_key, item_value in list(first_item.items())[:5]:
                                print(f"      {item_key}: {item_value} ({type(item_value)})")
                    
                    elif isinstance(value, (str, int, float, bool)):
                        print(f"   Value: {value}")
                    elif value is None:
                        print(f"   Value: None")
                    else:
                        print(f"   Complex type, length: {len(value) if hasattr(value, '__len__') else 'N/A'}")
            
            # Try brand search with different approaches
            print(f"\n🔍 Testing brand search with 'Nike':")
            
            search_response = api.session.get(f"{api.base_url}/brands/", params={"search": "Nike"})
            if search_response.status_code == 200:
                search_data = search_response.json()
                
                print(f"Search results count: {search_data.get('count', 'N/A')}")
                search_results = search_data.get('results', [])
                
                if search_results:
                    print(f"First search result:")
                    first_result = search_results[0]
                    for key, value in first_result.items():
                        print(f"   {key}: {value}")
                else:
                    print("No results in search response")
        
        # Try accessing a specific brand page if possible
        print(f"\n🔍 Testing paginated brand access:")
        page_response = api.session.get(f"{api.base_url}/brands/", params={"page": 1, "page_size": 5})
        if page_response.status_code == 200:
            page_data = page_response.json()
            results = page_data.get('results', [])
            
            if results:
                print(f"Sample brands from page 1:")
                for i, brand in enumerate(results[:3]):
                    print(f"\nBrand {i+1}:")
                    for key, value in brand.items():
                        print(f"   {key}: {value}")
                        
                    # If we find a brand with an ID, try to get its products
                    brand_id = brand.get('id')
                    if brand_id:
                        print(f"\n   🔍 Trying to find products for brand ID {brand_id}:")
                        
                        # Test different product endpoints
                        product_endpoints = [
                            f"/brands/{brand_id}/products/",
                            f"/products/?brand={brand_id}",
                            f"/catalog/?brand={brand_id}",
                        ]
                        
                        for endpoint in product_endpoints:
                            try:
                                prod_response = api.session.get(f"{api.base_url}{endpoint}")
                                print(f"      {endpoint}: Status {prod_response.status_code}")
                                
                                if prod_response.status_code == 200:
                                    prod_data = prod_response.json()
                                    if isinstance(prod_data, dict) and 'results' in prod_data:
                                        print(f"         Found {len(prod_data['results'])} products!")
                                        if prod_data['results']:
                                            first_product = prod_data['results'][0]
                                            print(f"         First product keys: {list(first_product.keys())}")
                                            return endpoint, prod_data
                                    elif isinstance(prod_data, list):
                                        print(f"         Found {len(prod_data)} products!")
                                        if prod_data:
                                            print(f"         First product keys: {list(prod_data[0].keys())}")
                                            return endpoint, prod_data
                                            
                            except Exception as e:
                                print(f"      {endpoint}: Error {e}")
                        
    except Exception as e:
        print(f"❌ Error analyzing response: {e}")
    
    return None, None


def main():
    """Main analysis function"""
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
    
    endpoint, data = analyze_response_structure(api)
    
    if endpoint and data:
        print(f"\n🎉 SUCCESS! Found product endpoint: {endpoint}")
        print(f"Sample product data structure discovered!")
    else:
        print(f"\n🤔 Product endpoint not yet discovered. May need different approach.")


if __name__ == "__main__":
    main()
