#!/usr/bin/env python3
"""
Simple test to check Keepa API dimension data
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from core.keepa_api import KeepaAPI
    from utils.config import Config
    print("✅ Successfully imported KeepaAPI")
    
    # Load config to get API key
    config = Config()
    api_key = config.get('keepa_api_key')
    print(f"✅ Found API key: {api_key[:10]}...")
    
    # Test basic API initialization
    api = KeepaAPI(api_key)
    print("✅ API initialized")
    
    # Quick test - just check if we can call the method
    print("Testing with ASIN: B0BQBXBW88")
    result = api.get_product_data('B0BQBXBW88')
    
    if result and isinstance(result, dict):
        print(f"✅ API call completed. Result keys: {list(result.keys())}")
        
        # Check raw_data for dimensions
        if 'raw_data' in result:
            raw_data = result['raw_data']
            print(f"\n🔍 Raw data available")
            
            # Raw data IS the product data in this case
            print(f"\n📦 Extracting dimension data from raw_data...")
            
            # Check for dimension fields directly in raw_data
            dimension_fields = [
                'packageHeight', 'packageLength', 'packageWidth', 'packageWeight',
                'itemHeight', 'itemLength', 'itemWidth', 'itemWeight'
            ]
            
            print("\n📦 Dimension data:")
            found_dimensions = {}
            for field in dimension_fields:
                value = raw_data.get(field)
                if value is not None:
                    unit = 'mm' if 'Height' in field or 'Length' in field or 'Width' in field else 'grams'
                    print(f"  ✅ {field}: {value} {unit}")
                    found_dimensions[field] = value
                else:
                    print(f"  ❌ {field}: Not available")
            
            if found_dimensions:
                print(f"\n✅ Found {len(found_dimensions)} dimension fields!")
                
                # Calculate volume if package dimensions available
                pkg_length = raw_data.get('packageLength')
                pkg_width = raw_data.get('packageWidth')
                pkg_height = raw_data.get('packageHeight')
                pkg_weight = raw_data.get('packageWeight')
                
                if all([pkg_length, pkg_width, pkg_height]):
                    volume_m3 = (pkg_length * pkg_width * pkg_height) / (1000**3)
                    print(f"\n📏 Volume calculation:")
                    print(f"  Dimensions: {pkg_length}mm × {pkg_width}mm × {pkg_height}mm")
                    print(f"  Volume: {volume_m3:.6f} cubic meters")
                    
                    # Size classification for Amazon fees
                    weight_kg = pkg_weight / 1000 if pkg_weight else 0
                    max_dim = max(pkg_length, pkg_width, pkg_height)
                    
                    # Amazon size criteria: 45cm × 34cm × 26cm, 12kg, max side 45cm
                    if (max_dim <= 450 and weight_kg <= 12 and 
                        pkg_length <= 450 and pkg_width <= 340 and pkg_height <= 260):
                        size_cat = 'Standard-size'
                        rate = 26.00  # €/m³/month
                    else:
                        size_cat = 'Oversize'  
                        rate = 18.60  # €/m³/month
                        
                    print(f"  Size category: {size_cat}")
                    print(f"  Storage rate: €{rate}/m³/month")
                    
                    # 3-month storage cost
                    storage_cost = volume_m3 * rate * 3
                    print(f"  3-month storage cost: €{storage_cost:.4f}")
                else:
                    print(f"\n⚠️ Missing package dimensions for volume calculation")
            else:
                print(f"\n⚠️ No dimension data found")
        else:
            print(f"❌ No 'raw_data' field in result")
            
        print(f"\n📋 Product info from processed data:")
        print(f"  Title: {result.get('title', 'N/A')}")
        print(f"  Current price: {result.get('current_price', 'N/A')}")
        print(f"  Weight: {result.get('weight', 'N/A')}")
    else:
        print(f"❌ No result or wrong format: {result}")
        
except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n✅ Test completed")
