#!/usr/bin/env python3
"""
Test script for enhanced ROI calculator
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from core.enhanced_roi_calculator import EnhancedROICalculator
    from core.keepa_api import KeepaAPI
    from utils.config import Config
    print("✅ Successfully imported enhanced ROI calculator")
    
    # Initialize enhanced ROI calculator
    config = Config()
    roi_calculator = EnhancedROICalculator(config=config)
    print("✅ Enhanced ROI calculator initialized")
    
    # Test data based on our L'Oréal product
    cost_price = 8.50  # Your purchase cost
    selling_price = 12.89  # Amazon selling price
    weight_kg = 0.11  # Product weight
    category = 'beauty'  # Product category
    
    print(f"\n📊 Testing comprehensive ROI calculation:")
    print(f"  Cost price: €{cost_price}")
    print(f"  Selling price: €{selling_price}")
    print(f"  Weight: {weight_kg} kg")
    print(f"  Category: {category}")
    
    # Basic calculation without Keepa data
    basic_result = roi_calculator.calculate_comprehensive_roi(
        cost_price=cost_price,
        selling_price=selling_price,
        weight_kg=weight_kg,
        category=category
    )
    
    print(f"\n💰 Basic ROI Results:")
    print(f"  Total Amazon fees: €{basic_result['total_amazon_fees']:.4f}")
    print(f"  Net proceeds: €{basic_result['net_proceeds']:.4f}")
    print(f"  Profit: €{basic_result['profit']:.4f}")
    print(f"  ROI: {basic_result['roi_percentage']:.2f}%")
    print(f"  Profit margin: {basic_result['profit_margin']:.2f}%")
    print(f"  Profitability score: {basic_result['profitability_score']:.1f}/100")
    print(f"  Is profitable: {basic_result['is_profitable']}")
    
    # Test with Keepa data
    print(f"\n🔍 Testing with Keepa data...")
    api_key = config.get('keepa_api_key')
    if api_key:
        try:
            keepa_api = KeepaAPI(api_key)
            keepa_result = keepa_api.get_product_data('B0BQBXBW88')
            
            if keepa_result and keepa_result.get('raw_data'):
                keepa_data = keepa_result['raw_data']
                
                enhanced_result = roi_calculator.calculate_comprehensive_roi(
                    cost_price=cost_price,
                    selling_price=selling_price,
                    weight_kg=weight_kg,
                    category=category,
                    keepa_data=keepa_data
                )
                
                print(f"\n💰 Enhanced ROI Results (with Keepa data):")
                print(f"  Total Amazon fees: €{enhanced_result['total_amazon_fees']:.4f}")
                print(f"  Net proceeds: €{enhanced_result['net_proceeds']:.4f}")
                print(f"  Profit: €{enhanced_result['profit']:.4f}")
                print(f"  ROI: {enhanced_result['roi_percentage']:.2f}%")
                print(f"  Profit margin: {enhanced_result['profit_margin']:.2f}%")
                print(f"  Profitability score: {enhanced_result['profitability_score']:.1f}/100")
                
                # Show detailed fee breakdown
                fees_breakdown = enhanced_result['amazon_fees_breakdown']
                print(f"\n📋 Detailed Fee Breakdown:")
                print(f"  Referral fee: €{fees_breakdown['referral_fee']:.4f}")
                print(f"  FBA fee: €{fees_breakdown['fba_fee']:.4f}")
                print(f"  Storage fee: €{fees_breakdown['storage_fee']:.4f}")
                print(f"  Prep fee: €{fees_breakdown['prep_fee']:.4f}")
                print(f"  Inbound shipping: €{fees_breakdown['inbound_shipping']:.4f}")
                print(f"  Digital services: €{fees_breakdown['digital_services']:.4f}")
                print(f"  Misc fee: €{fees_breakdown['misc_fee']:.4f}")
                print(f"  VAT on fees: €{fees_breakdown['vat_on_fees']:.4f}")
                
                # Show calculation notes
                notes = enhanced_result['calculation_notes']
                if notes:
                    print(f"\n📝 Calculation Notes:")
                    for note in notes:
                        print(f"  • {note}")
                
                # Test break-even calculation
                print(f"\n🎯 Break-even Analysis:")
                breakeven = roi_calculator.calculate_break_even_price(
                    cost_price=cost_price,
                    weight_kg=weight_kg,
                    category=category,
                    target_roi=20.0,  # Target 20% ROI
                    keepa_data=keepa_data
                )
                
                print(f"  Target ROI: {breakeven['target_roi']:.1f}%")
                print(f"  Break-even price: €{breakeven['break_even_price']:.2f}")
                print(f"  Achieved ROI: {breakeven['achieved_roi']:.2f}%")
                print(f"  Calculation iterations: {breakeven['iterations']}")
                
            else:
                print("❌ No Keepa data available")
        except Exception as e:
            print(f"❌ Keepa API error: {e}")
    else:
        print("❌ No Keepa API key configured")
    
    print(f"\n✅ Enhanced ROI calculator test completed successfully!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
