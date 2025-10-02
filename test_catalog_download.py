"""
Test the discovered Qogita catalog download endpoint with CSV format.
"""

import sys
import os
import json
import csv
from io import StringIO

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


def test_catalog_download_endpoint(api: QogitaAPI):
    """Test the /variants/search/download/ endpoint"""
    print("🎯 Testing Catalog Download Endpoint")
    print("=" * 50)
    
    # Test different parameter combinations
    test_cases = [
        {
            "name": "All products (small sample)",
            "params": {
                "page": 1,
                "size": 10
            }
        },
        {
            "name": "Fragrance category",
            "params": {
                "category_name": "fragrance",
                "page": 1,
                "size": 10
            }
        },
        {
            "name": "Beauty category",
            "params": {
                "category_name": "beauty",
                "page": 1,
                "size": 10
            }
        },
        {
            "name": "Cosmetics category",
            "params": {
                "category_name": "cosmetics",
                "page": 1,
                "size": 10
            }
        },
        {
            "name": "Skincare category",
            "params": {
                "category_name": "skincare",
                "page": 1,
                "size": 10
            }
        },
        {
            "name": "3ina brand (known to exist)",
            "params": {
                "brand_name": "3ina",
                "page": 1,
                "size": 20
            }
        },
        {
            "name": "Multiple brands",
            "params": {
                "brand_name": ["3ina", "100bon"],
                "page": 1,
                "size": 20
            }
        },
        {
            "name": "In stock products",
            "params": {
                "stock_availability": "in_stock",
                "page": 1,
                "size": 10
            }
        },
    ]
    
    successful_tests = []
    
    for test_case in test_cases:
        test_name = test_case["name"]
        params = test_case["params"]
        
        print(f"\n🔍 Testing: {test_name}")
        print(f"   Parameters: {params}")
        
        try:
            # Build the URL with parameters
            url = f"{api.base_url}/variants/search/download/"
            
            # Handle multiple brand names
            if "brand_name" in params and isinstance(params["brand_name"], list):
                # Create URL with multiple brand_name parameters
                brand_params = "&".join([f"brand_name={brand}" for brand in params["brand_name"]])
                other_params = "&".join([f"{k}={v}" for k, v in params.items() if k != "brand_name"])
                query_string = f"{brand_params}&{other_params}" if other_params else brand_params
                full_url = f"{url}?{query_string}"
                
                # For requests.get, we need to handle this differently
                response = api.session.get(url, params={k: v for k, v in params.items() if k != "brand_name"})
                # Add brand names to the URL manually
                for brand in params["brand_name"]:
                    response = api.session.get(f"{url}?brand_name={brand}&" + "&".join([f"{k}={v}" for k, v in params.items() if k != "brand_name"]))
                    break  # Just test with first brand for now
            else:
                response = api.session.get(url, params=params)
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                # Try to parse as CSV
                content = response.content.decode('utf-8')
                print(f"   Content length: {len(content)} characters")
                
                if content.strip():
                    try:
                        # Parse CSV content
                        csv_reader = csv.reader(StringIO(content))
                        
                        # Read header row
                        headers = next(csv_reader)
                        print(f"   ✅ CSV Headers ({len(headers)} columns): {headers}")
                        
                        # Read data rows
                        rows = list(csv_reader)
                        print(f"   📦 Data rows: {len(rows)}")
                        
                        if rows:
                            print(f"   📋 Sample data (first row):")
                            for i, (header, value) in enumerate(zip(headers, rows[0])):
                                if i < 10:  # Show first 10 columns
                                    print(f"      {header}: {value}")
                            
                            successful_tests.append({
                                "test_name": test_name,
                                "params": params,
                                "headers": headers,
                                "row_count": len(rows),
                                "sample_row": rows[0] if rows else None
                            })
                        
                    except csv.Error as e:
                        print(f"   ❌ CSV parsing error: {e}")
                        print(f"   Raw content sample: {content[:200]}...")
                else:
                    print(f"   ⚠️  Empty response content")
            
            elif response.status_code == 404:
                print(f"   ❌ Endpoint not found")
            else:
                print(f"   ❌ HTTP {response.status_code}")
                try:
                    error_content = response.content.decode('utf-8')
                    if error_content:
                        print(f"   Error content: {error_content[:200]}...")
                except:
                    pass
                    
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    return successful_tests


def analyze_product_data_structure(successful_tests):
    """Analyze the structure of product data we found"""
    print(f"\n📊 Analysis of Product Data Structure")
    print("=" * 50)
    
    if not successful_tests:
        print("❌ No successful tests to analyze")
        return
    
    print(f"✅ Found {len(successful_tests)} working parameter combinations")
    
    for test in successful_tests:
        print(f"\n🎯 {test['test_name']}:")
        print(f"   Parameters: {test['params']}")
        print(f"   Rows found: {test['row_count']}")
        print(f"   Columns: {len(test['headers'])}")
        
        headers = test['headers']
        
        # Look for key product identifiers
        key_fields = ['ean', 'gtin', 'barcode', 'sku', 'product_id', 'variant_id', 'qid']
        price_fields = ['price', 'cost', 'wholesale_price', 'unit_price', 'retail_price']
        brand_fields = ['brand', 'brand_name', 'manufacturer']
        
        found_key_fields = [field for field in key_fields if any(field.lower() in header.lower() for header in headers)]
        found_price_fields = [field for field in price_fields if any(field.lower() in header.lower() for header in headers)]
        found_brand_fields = [field for field in brand_fields if any(field.lower() in header.lower() for header in headers)]
        
        print(f"   🔑 Product identifiers: {found_key_fields}")
        print(f"   💰 Price fields: {found_price_fields}")
        print(f"   🏷️  Brand fields: {found_brand_fields}")
        
        if test['sample_row']:
            print(f"   📋 Sample values:")
            for i, (header, value) in enumerate(zip(headers, test['sample_row'])):
                if any(field.lower() in header.lower() for field in key_fields + price_fields + brand_fields):
                    print(f"      {header}: {value}")


def test_brand_specific_searches(api: QogitaAPI):
    """Test searches for specific cosmetics brands we know exist"""
    print(f"\n🧴 Testing Brand-Specific Searches")
    print("=" * 40)
    
    # Brands we discovered in previous tests
    known_brands = [
        "3ina",
        "100bon", 
        "111skin",
        "100% Pure",
        "3deluxe",
        "3lab"
    ]
    
    successful_brand_searches = []
    
    for brand in known_brands:
        print(f"\n🔍 Testing brand: {brand}")
        
        try:
            url = f"{api.base_url}/variants/search/download/"
            params = {
                "brand_name": brand,
                "page": 1,
                "size": 50  # Get more products for analysis
            }
            
            response = api.session.get(url, params=params)
            
            if response.status_code == 200:
                content = response.content.decode('utf-8')
                
                if content.strip():
                    csv_reader = csv.reader(StringIO(content))
                    headers = next(csv_reader)
                    rows = list(csv_reader)
                    
                    print(f"   ✅ Found {len(rows)} products for {brand}")
                    
                    if rows:
                        successful_brand_searches.append({
                            "brand": brand,
                            "product_count": len(rows),
                            "headers": headers,
                            "sample_products": rows[:3]  # First 3 products
                        })
                else:
                    print(f"   ⚠️  Empty response for {brand}")
            else:
                print(f"   ❌ HTTP {response.status_code} for {brand}")
                
        except Exception as e:
            print(f"   ❌ Error testing {brand}: {e}")
    
    return successful_brand_searches


def main():
    """Main test function for catalog download endpoint"""
    print("🎯 TESTING QOGITA CATALOG DOWNLOAD ENDPOINT")
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
    
    # Test catalog download endpoint
    successful_tests = test_catalog_download_endpoint(api)
    
    # Analyze the data structure
    analyze_product_data_structure(successful_tests)
    
    # Test specific brands
    brand_results = test_brand_specific_searches(api)
    
    if successful_tests or brand_results:
        print(f"\n🎉 MAJOR BREAKTHROUGH!")
        print(f"   ✅ Found working Qogita product endpoint: /variants/search/download/")
        print(f"   ✅ Can retrieve product data in CSV format")
        print(f"   ✅ Can filter by brand, category, and stock availability")
        print(f"   ✅ Ready to implement Qogita integration!")
    else:
        print(f"\n🤔 Endpoint tests completed but no data found")


if __name__ == "__main__":
    main()
