"""
Test Qogita API with cosmetics brands like L'Oréal, Wella, etc.
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


def search_cosmetics_brands(api: QogitaAPI):
    """Search for cosmetics brands specifically"""
    print("🔍 Searching for Cosmetics Brands")
    print("=" * 50)
    
    cosmetics_brands = [
        "L'Oréal", "Loreal", "L'Oreal",
        "Wella", 
        "Maybelline",
        "Garnier",
        "Revlon",
        "CoverGirl", "Cover Girl",
        "Estée Lauder", "Estee Lauder",
        "MAC",
        "Clinique",
        "Lancôme", "Lancome",
        "Yves Saint Laurent", "YSL",
        "Chanel",
        "Dior",
        "Urban Decay",
        "Benefit",
        "Too Faced",
        "Sephora",
        "NYX",
        "Rimmel",
        "Max Factor",
        "Bourjois",
        "Essence",
        "Catrice",
        "Schwarzkopf",
        "Tresemmé", "Tresemme",
        "Pantene",
        "Head & Shoulders",
        "Herbal Essences",
        "Dove",
        "Nivea",
        "Olay",
        "Neutrogena",
        "La Roche-Posay"
    ]
    
    found_brands = {}
    
    for brand_name in cosmetics_brands:
        print(f"\n🔍 Searching for: '{brand_name}'")
        
        # Try exact match search
        try:
            response = api.session.get(f"{api.base_url}/brands/", params={"search": brand_name})
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                
                # Look for exact or close matches
                matches = []
                for brand in results:
                    brand_result_name = brand.get('name', '').lower()
                    search_name = brand_name.lower()
                    
                    if (search_name in brand_result_name or 
                        brand_result_name in search_name or
                        brand_result_name == search_name):
                        matches.append(brand)
                
                if matches:
                    print(f"   ✅ Found {len(matches)} matches:")
                    for match in matches:
                        brand_name_found = match.get('name')
                        brand_qid = match.get('qid')
                        variant_count = match.get('variantCount', 0)
                        
                        print(f"      • {brand_name_found} (QID: {brand_qid}, {variant_count} variants)")
                        
                        if variant_count > 0:
                            found_brands[brand_name_found] = {
                                'qid': brand_qid,
                                'variant_count': variant_count,
                                'search_term': brand_name
                            }
                else:
                    print(f"   ❌ No matches found")
            else:
                print(f"   ❌ Search failed: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    return found_brands


def test_variant_discovery_for_cosmetics(api: QogitaAPI, brands_dict):
    """Try to find variants/products for cosmetics brands"""
    print(f"\n🧴 Testing Variant Discovery for Cosmetics Brands")
    print("=" * 60)
    
    for brand_name, brand_info in list(brands_dict.items())[:5]:  # Test first 5 brands
        brand_qid = brand_info['qid']
        variant_count = brand_info['variant_count']
        
        print(f"\n📦 Testing brand: {brand_name}")
        print(f"   QID: {brand_qid}")
        print(f"   Expected variants: {variant_count}")
        
        # Try different approaches to get variants
        endpoints_to_try = [
            # Direct brand detail
            f"/brands/{brand_qid}/",
            
            # Variant searches
            f"/variants/?brand={brand_qid}",
            f"/variants/?brand_qid={brand_qid}",
            f"/variants/?brand_name={brand_name}",
            
            # Product searches  
            f"/products/?brand={brand_qid}",
            f"/products/?brand_qid={brand_qid}",
            
            # Catalog searches
            f"/catalog/?brand={brand_qid}",
            f"/catalog/variants/?brand={brand_qid}",
            
            # Search endpoints
            f"/search/?brand={brand_qid}",
            f"/search/variants/?brand={brand_qid}",
            f"/search/products/?brand={brand_qid}",
        ]
        
        for endpoint in endpoints_to_try:
            try:
                response = api.session.get(f"{api.base_url}{endpoint}")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    print(f"   ✅ {endpoint}")
                    
                    if isinstance(data, dict):
                        if 'results' in data and data['results']:
                            results = data['results']
                            print(f"      📦 Found {len(results)} items")
                            
                            # Analyze first result for product-like data
                            first_item = results[0]
                            print(f"      🔍 First item keys: {list(first_item.keys())}")
                            
                            # Look for product identifiers
                            product_identifiers = ['ean', 'gtin', 'barcode', 'sku', 'product_id']
                            price_fields = ['price', 'cost', 'wholesale_price', 'unit_price']
                            
                            found_identifiers = [field for field in product_identifiers if field in first_item]
                            found_prices = [field for field in price_fields if field in first_item]
                            
                            if found_identifiers:
                                print(f"      🎯 Product identifiers: {found_identifiers}")
                            if found_prices:
                                print(f"      💰 Price fields: {found_prices}")
                            
                            if found_identifiers or found_prices:
                                print(f"      📋 Sample product data:")
                                for key, value in list(first_item.items())[:8]:
                                    print(f"         {key}: {value}")
                                
                                return endpoint, data  # Found products!
                        
                        elif 'variants' in data or 'products' in data:
                            print(f"      🎯 Contains product data in structure!")
                            print(f"      📋 Keys: {list(data.keys())}")
                            return endpoint, data
                        
                        else:
                            print(f"      📋 Response keys: {list(data.keys())}")
                    
                    elif isinstance(data, list) and data:
                        print(f"      📦 Found {len(data)} items in list")
                        first_item = data[0]
                        print(f"      🔍 First item keys: {list(first_item.keys())}")
                        
                        # Check for product data
                        product_identifiers = ['ean', 'gtin', 'barcode', 'sku', 'product_id']
                        found_identifiers = [field for field in product_identifiers if field in first_item]
                        
                        if found_identifiers:
                            print(f"      🎯 Product identifiers found: {found_identifiers}")
                            return endpoint, data
                
                elif response.status_code == 404:
                    print(f"   ❌ {endpoint} - Not found")
                else:
                    print(f"   ⚠️  {endpoint} - Status: {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ {endpoint} - Error: {e}")
    
    return None, None


def test_known_cosmetics_gtins(api: QogitaAPI):
    """Test the /variants/{search}/ endpoint with known cosmetics GTINs"""
    print(f"\n🔍 Testing Known Cosmetics GTINs with /variants/ endpoint")
    print("=" * 60)
    
    # Some common cosmetics GTINs (these are examples, might not be in Qogita)
    test_gtins = [
        "3600523951416",  # L'Oréal product example
        "4015600720469",  # Schwarzkopf example
        "8411061924204",  # Wella example
        "3346470138018",  # Lancôme example
        "3607346648567",  # Maybelline example
    ]
    
    for gtin in test_gtins:
        print(f"\n🔍 Testing GTIN: {gtin}")
        
        try:
            # Test the variants search endpoint
            response = api.session.get(f"{api.base_url}/variants/{gtin}/")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Found product data!")
                print(f"   📋 Response keys: {list(data.keys()) if isinstance(data, dict) else 'List response'}")
                
                if isinstance(data, dict):
                    for key, value in list(data.items())[:10]:
                        print(f"      {key}: {value}")
                
                return gtin, data
                
            elif response.status_code == 404:
                print(f"   ❌ GTIN not found")
            else:
                print(f"   ⚠️  Status: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    return None, None


def main():
    """Main cosmetics testing function"""
    print("🧴 Qogita Cosmetics Brand Discovery")
    print("=" * 50)
    
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
    
    # 1. Search for cosmetics brands
    found_brands = search_cosmetics_brands(api)
    
    print(f"\n📊 Summary: Found {len(found_brands)} cosmetics brands with variants")
    for name, info in found_brands.items():
        print(f"   • {name}: {info['variant_count']} variants")
    
    if found_brands:
        # 2. Try to discover variant/product endpoints
        endpoint, data = test_variant_discovery_for_cosmetics(api, found_brands)
        
        if endpoint and data:
            print(f"\n🎉 SUCCESS! Found cosmetics products at: {endpoint}")
            return
    
    # 3. Test with known GTINs
    gtin, data = test_known_cosmetics_gtins(api)
    
    if gtin and data:
        print(f"\n🎉 SUCCESS! Found product via GTIN: {gtin}")
    else:
        print(f"\n🤔 Still exploring cosmetics endpoints...")


if __name__ == "__main__":
    main()
