#!/usr/bin/env python3
"""
Test script to verify dimension data extraction from Keepa API
"""

from core.keepa_api import KeepaAPI
import json

def test_dimension_extraction():
    # Initialize API
    api = KeepaAPI()
    
    # Test with our known ASIN
    asin = 'B0BQBXBW88'
    print(f'Testing dimension extraction for ASIN: {asin}')
    print('=' * 50)
    
    try:
        result = api.get_product_data(asin)
        if result and 'success' in result and result['success']:
            product = result.get('product', {})
            
            print('Available dimension fields:')
            dimension_fields = ['packageHeight', 'packageLength', 'packageWidth', 'packageWeight', 
                              'itemHeight', 'itemLength', 'itemWidth']
            
            for field in dimension_fields:
                value = product.get(field)
                if value:
                    unit = 'mm' if 'Height' in field or 'Length' in field or 'Width' in field else 'grams'
                    print(f'  {field}: {value} {unit}')
                else:
                    print(f'  {field}: Not available')
            
            # Calculate volume if dimensions available
            pkg_length = product.get('packageLength')
            pkg_width = product.get('packageWidth') 
            pkg_height = product.get('packageHeight')
            
            if all([pkg_length, pkg_width, pkg_height]):
                volume_m3 = (pkg_length * pkg_width * pkg_height) / (1000**3)
                print(f'\nCalculated volume: {volume_m3:.6f} cubic meters')
                
                # Size classification
                pkg_weight = product.get('packageWeight', 0)
                weight_kg = pkg_weight / 1000 if pkg_weight else 0
                max_dim = max(pkg_length, pkg_width, pkg_height)
                
                if (max_dim <= 450 and weight_kg <= 12 and 
                    pkg_length <= 450 and pkg_width <= 340 and pkg_height <= 260):
                    size_cat = 'Standard-size'
                    rate = 26.00
                else:
                    size_cat = 'Oversize'  
                    rate = 18.60
                    
                print(f'Size category: {size_cat}')
                print(f'Storage rate: €{rate}/m³/month')
                
                # 3-month storage cost
                storage_cost = volume_m3 * rate * 3
                print(f'3-month storage cost: €{storage_cost:.4f}')
            else:
                print('\nDimensions not available for volume calculation')
                
        else:
            print('Failed to get product data')
            if result:
                print(f'Error details: {result}')
            
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_dimension_extraction()
