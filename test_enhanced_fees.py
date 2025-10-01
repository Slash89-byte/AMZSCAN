#!/usr/bin/env python3
"""
Test script for enhanced Amazon fees calculator
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from core.enhanced_amazon_fees import EnhancedAmazonFeesCalculator
    from core.keepa_api import KeepaAPI
    from utils.config import Config
    print("✅ Successfully imported enhanced calculator")
    
    # Initialize enhanced calculator
    config = Config()
    calculator = EnhancedAmazonFeesCalculator(config=config)
    print("✅ Enhanced calculator initialized")
    
    # Test with basic calculation first
    selling_price = 12.89
    weight_kg = 0.11
    category = 'beauty'
    
    print(f"\n📊 Testing basic fee calculation:")
    print(f"  Selling price: €{selling_price}")
    print(f"  Weight: {weight_kg} kg")
    print(f"  Category: {category}")
    
    basic_result = calculator.calculate_comprehensive_fees(
        selling_price=selling_price,
        weight_kg=weight_kg,
        category=category
    )
    
    print(f"\n💰 Basic Fee Breakdown:")
    print(f"  Referral fee: €{basic_result['referral_fee']:.4f}")
    print(f"  FBA fee: €{basic_result['fba_fee']:.4f}")
    print(f"  Closing fee: €{basic_result['closing_fee']:.4f}")
    print(f"  Storage fee: €{basic_result['storage_fee']:.4f}")
    print(f"  Total fees: €{basic_result['total_fees']:.4f}")
    print(f"  Net proceeds: €{basic_result['net_proceeds']:.4f}")
    
    # Test with Keepa data
    print(f"\n🔍 Testing with Keepa data...")
    api_key = config.get('keepa_api_key')
    if api_key:
        try:
            keepa_api = KeepaAPI(api_key)
            keepa_result = keepa_api.get_product_data('B0BQBXBW88')
            
            if keepa_result and keepa_result.get('raw_data'):
                keepa_data = keepa_result['raw_data']
                
                enhanced_result = calculator.calculate_comprehensive_fees(
                    selling_price=selling_price,
                    weight_kg=weight_kg,
                    category=category,
                    keepa_data=keepa_data
                )
                
                print(f"\n💰 Enhanced Fee Breakdown (with Keepa data):")
                print(f"  Referral fee: €{enhanced_result['referral_fee']:.4f}")
                print(f"  FBA fee: €{enhanced_result['fba_fee']:.4f}")
                print(f"  Storage fee: €{enhanced_result['storage_fee']:.4f}")
                print(f"  Total fees: €{enhanced_result['total_fees']:.4f}")
                print(f"  Net proceeds: €{enhanced_result['net_proceeds']:.4f}")
                
                storage_details = enhanced_result['storage_details']
                if storage_details['calculation_possible']:
                    print(f"\n📦 Storage Calculation Details:")
                    print(f"  Volume: {storage_details['volume_m3']:.6f} m³")
                    print(f"  Size category: {storage_details['size_category']}")
                    print(f"  Rate: €{storage_details['rate_per_m3']}/m³/month")
                    print(f"  Storage months: {storage_details['storage_months']}")
                else:
                    print(f"  ⚠️ {storage_details.get('warning', 'Storage calculation not possible')}")
            else:
                print("❌ No Keepa data available")
        except Exception as e:
            print(f"❌ Keepa API error: {e}")
    else:
        print("❌ No Keepa API key configured")
    
    print(f"\n✅ Enhanced calculator test completed successfully!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
