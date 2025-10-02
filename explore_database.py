"""
Explore actual brands in Qogita database to understand their product catalog.
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


def explore_brands_database(api: QogitaAPI, max_pages=10):
    """Explore the actual brands in Qogita's database"""
    print("🔍 Exploring Qogita Brands Database")
    print("=" * 50)
    
    all_brands = []
    brands_with_variants = []
    
    for page in range(1, max_pages + 1):
        print(f"\n📄 Page {page}:")
        
        try:
            response = api.session.get(f"{api.base_url}/brands/", params={"page": page, "page_size": 50})
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                
                if not results:
                    print(f"   ❌ No more results on page {page}")
                    break
                
                print(f"   📦 Found {len(results)} brands")
                
                for brand in results:
                    brand_name = brand.get('name', 'Unknown')
                    brand_qid = brand.get('qid')
                    variant_count = brand.get('variantCount', 0)
                    description = brand.get('description', '').strip()
                    
                    all_brands.append(brand)
                    
                    if variant_count > 0:
                        brands_with_variants.append(brand)
                        
                        # Show brands with many variants (likely established brands)
                        if variant_count >= 10:
                            desc_preview = description[:50] + "..." if len(description) > 50 else description
                            print(f"      🎯 {brand_name} ({variant_count} variants) - {desc_preview}")
            else:
                print(f"   ❌ Failed to get page {page}: {response.status_code}")
                break
                
        except Exception as e:
            print(f"   ❌ Error on page {page}: {e}")
            break
    
    return all_brands, brands_with_variants


def analyze_brand_patterns(brands_with_variants):
    """Analyze patterns in brands with variants"""
    print(f"\n📊 Analysis of Brands with Variants")
    print("=" * 50)
    
    print(f"Total brands with variants: {len(brands_with_variants)}")
    
    # Sort by variant count
    sorted_brands = sorted(brands_with_variants, key=lambda x: x.get('variantCount', 0), reverse=True)
    
    print(f"\n🏆 Top 20 Brands by Variant Count:")
    for i, brand in enumerate(sorted_brands[:20]):
        brand_name = brand.get('name')
        variant_count = brand.get('variantCount', 0)
        description = brand.get('description', '').strip()
        qid = brand.get('qid')
        
        desc_preview = description[:60] + "..." if len(description) > 60 else description
        print(f"   {i+1:2d}. {brand_name} ({variant_count} variants)")
        if desc_preview:
            print(f"       {desc_preview}")
        print(f"       QID: {qid}")
    
    # Look for cosmetics-related keywords
    cosmetics_keywords = [
        'beauty', 'cosmetic', 'makeup', 'skincare', 'hair', 'fragrance', 
        'perfume', 'nail', 'lip', 'face', 'eye', 'cream', 'lotion',
        'shampoo', 'conditioner', 'serum', 'foundation', 'mascara'
    ]
    
    print(f"\n🧴 Brands with Cosmetics-Related Keywords:")
    cosmetics_brands = []
    
    for brand in brands_with_variants:
        brand_name = brand.get('name', '').lower()
        description = brand.get('description', '').lower()
        
        for keyword in cosmetics_keywords:
            if keyword in brand_name or keyword in description:
                cosmetics_brands.append(brand)
                variant_count = brand.get('variantCount', 0)
                print(f"   • {brand.get('name')} ({variant_count} variants)")
                if brand.get('description'):
                    print(f"     Description: {brand.get('description')[:100]}...")
                break
    
    return sorted_brands[:10], cosmetics_brands


def test_high_variant_brands(api: QogitaAPI, top_brands):
    """Test product discovery with brands that have many variants"""
    print(f"\n🔍 Testing Product Discovery with High-Variant Brands")
    print("=" * 60)
    
    for brand in top_brands[:3]:  # Test top 3 brands
        brand_name = brand.get('name')
        brand_qid = brand.get('qid')
        variant_count = brand.get('variantCount', 0)
        
        print(f"\n📦 Testing: {brand_name} ({variant_count} variants)")
        print(f"   QID: {brand_qid}")
        
        # Try various endpoint combinations
        test_endpoints = [
            # Standard REST patterns
            f"/brands/{brand_qid}/variants/",
            f"/brands/{brand_qid}/products/",
            f"/brands/{brand_qid}/items/",
            
            # Query parameter approaches
            f"/variants/?brand={brand_qid}",
            f"/variants/?brand_qid={brand_qid}",
            f"/products/?brand={brand_qid}",
            f"/products/?brand_qid={brand_qid}",
            
            # Alternative patterns from documentation
            f"/catalog/brands/{brand_qid}/",
            f"/catalog/variants/?brand={brand_qid}",
            f"/inventory/?brand={brand_qid}",
            
            # Search patterns
            f"/search/?q={brand_name}",
            f"/search/variants/?brand={brand_qid}",
            
            # Try brand slug instead of QID
            f"/brands/{brand.get('slug', brand_qid)}/variants/",
            f"/brands/{brand.get('slug', brand_qid)}/products/",
        ]
        
        for endpoint in test_endpoints:
            try:
                response = api.session.get(f"{api.base_url}{endpoint}")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    print(f"   ✅ SUCCESS: {endpoint}")
                    print(f"      Response type: {type(data)}")
                    
                    if isinstance(data, dict):
                        if 'results' in data:
                            results = data['results']
                            print(f"      📦 Found {len(results)} items in results")
                            
                            if results:
                                first_item = results[0]
                                print(f"      🔍 First item keys: {list(first_item.keys())}")
                                
                                # Check for product-specific fields
                                product_fields = ['ean', 'gtin', 'barcode', 'price', 'cost', 'wholesale_price', 'name', 'title', 'description']
                                found_fields = [field for field in product_fields if field in first_item]
                                
                                if found_fields:
                                    print(f"      🎯 Product fields found: {found_fields}")
                                    print(f"      📋 Sample data:")
                                    for field in found_fields[:5]:
                                        print(f"         {field}: {first_item[field]}")
                                    
                                    return endpoint, data  # Found products!
                        else:
                            print(f"      📋 Object keys: {list(data.keys())}")
                    
                    elif isinstance(data, list):
                        print(f"      📦 Found {len(data)} items in list")
                        if data:
                            first_item = data[0]
                            print(f"      🔍 First item keys: {list(first_item.keys())}")
                            
                            # Check for product fields
                            product_fields = ['ean', 'gtin', 'barcode', 'price', 'cost', 'wholesale_price']
                            found_fields = [field for field in product_fields if field in first_item]
                            
                            if found_fields:
                                print(f"      🎯 Product fields found: {found_fields}")
                                return endpoint, data
                
                elif response.status_code == 404:
                    continue  # Don't print all 404s
                else:
                    print(f"   ⚠️  {endpoint} - Status: {response.status_code}")
                    
            except Exception as e:
                continue  # Don't print all errors
    
    return None, None


def main():
    """Main exploration function"""
    print("🔍 Comprehensive Qogita Database Exploration")
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
    
    # 1. Explore brands database
    all_brands, brands_with_variants = explore_brands_database(api, max_pages=5)
    
    # 2. Analyze patterns
    top_brands, cosmetics_brands = analyze_brand_patterns(brands_with_variants)
    
    # 3. Test product discovery with top brands
    endpoint, data = test_high_variant_brands(api, top_brands)
    
    if endpoint and data:
        print(f"\n🎉 SUCCESS! Found products at: {endpoint}")
        print(f"This is the breakthrough we needed for Qogita integration!")
    else:
        print(f"\n🤔 Product endpoints still not discovered.")
        print(f"May need to check if API requires special permissions or different authentication scope.")


if __name__ == "__main__":
    main()
