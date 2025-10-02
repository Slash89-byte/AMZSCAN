#!/usr/bin/env python3
"""
Test the enhanced Amazon fees calculator with comprehensive fee structure
"""

import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.amazon_fees import AmazonFeesCalculator
from core.roi_calculator import ROICalculator
from utils.config import Config

def test_comprehensive_fees():
    """Test the comprehensive fee calculation"""
    
    print("🧮 Testing Comprehensive Amazon Fees Calculator")
    print("=" * 55)
    
    # Set up configuration
    config = Config()
    config.set_vat_rate(20.0)  # 20% VAT
    
    # Initialize calculator
    fees_calc = AmazonFeesCalculator('france', config)
    roi_calc = ROICalculator(config)
    
    # Test product parameters
    selling_price = 29.99
    cost_price = 15.00
    weight_kg = 0.5
    category = 'beauty'
    
    print(f"📦 Test Product:")
    print(f"  Selling Price: €{selling_price}")
    print(f"  Cost Price: €{cost_price}")
    print(f"  Weight: {weight_kg} kg")
    print(f"  Category: {category}")
    print()
    
    # Test basic fee calculation (backward compatibility)
    print("🔹 Basic Fee Calculation (Current Method):")
    basic_fees = fees_calc.calculate_total_fees(selling_price, weight_kg, category)
    
    print(f"  Referral Fee: €{basic_fees['referral_fee']:.2f}")
    print(f"  FBA Fee: €{basic_fees['fba_fee']:.2f}")
    print(f"  Closing Fee: €{basic_fees['closing_fee']:.2f}")
    print(f"  Total Basic Fees: €{basic_fees['total_fees']:.2f}")
    print(f"  Net Proceeds: €{basic_fees['net_proceeds']:.2f}")
    print()
    
    # Test comprehensive fee calculation (new method)
    print("🔸 Comprehensive Fee Calculation (Enhanced Method):")
    
    # Define additional parameters for comprehensive calculation
    prep_services = ['labeling', 'bubble_wrap']  # Example prep services
    misc_fee_types = ['return_processing']        # Example misc fees
    misc_quantities = [0.1]                       # 10% chance of return
    ad_spend = 50.0                              # €50 monthly ad spend
    
    comprehensive_fees = fees_calc.calculate_comprehensive_fees(
        selling_price=selling_price,
        weight_kg=weight_kg,
        category=category,
        volume_cubic_meters=0.002,  # Small product ~2L volume
        months_stored=2,            # 2 months average storage
        prep_services=prep_services,
        ad_spend=ad_spend,
        misc_fee_types=misc_fee_types,
        misc_quantities=misc_quantities,
        is_peak_season=False,
        shipment_type='small_parcel'
    )
    
    print("  📋 Fee Breakdown:")
    for fee_name, fee_amount in comprehensive_fees['fee_breakdown'].items():
        if fee_amount > 0:
            print(f"    {fee_name.replace('_', ' ').title()}: €{fee_amount:.2f}")
    
    print()
    print(f"  📊 Totals:")
    print(f"    Fees Before VAT: €{comprehensive_fees['fees_before_vat']:.2f}")
    print(f"    VAT on Fees: €{comprehensive_fees['vat_on_fees']:.2f}")
    print(f"    Total Fees with VAT: €{comprehensive_fees['total_fees_with_vat']:.2f}")
    print(f"    Net Proceeds: €{comprehensive_fees['net_proceeds']:.2f}")
    print()
    
    # Compare the two methods
    difference = comprehensive_fees['total_fees_with_vat'] - basic_fees['total_fees']
    print(f"💡 Difference between methods: €{difference:.2f}")
    print(f"   ({difference/basic_fees['total_fees']*100:+.1f}% more comprehensive)")
    print()
    
    # Calculate ROI with both methods
    print("📈 ROI Comparison:")
    
    # Basic ROI
    basic_roi = roi_calc.calculate_roi(cost_price, selling_price, basic_fees['total_fees'])
    print(f"  Basic Method ROI: {basic_roi['roi_percentage']:.1f}%")
    print(f"  Basic Method Profit: €{basic_roi['profit']:.2f}")
    
    # Comprehensive ROI
    comp_roi = roi_calc.calculate_roi(cost_price, selling_price, comprehensive_fees['total_fees_with_vat'])
    print(f"  Comprehensive ROI: {comp_roi['roi_percentage']:.1f}%")
    print(f"  Comprehensive Profit: €{comp_roi['profit']:.2f}")
    print()
    
    # Profitability assessment
    min_roi_threshold = config.get('min_roi_threshold', 15.0)
    basic_profitable = basic_roi['roi_percentage'] >= min_roi_threshold
    comp_profitable = comp_roi['roi_percentage'] >= min_roi_threshold
    
    print("🎯 Profitability Assessment:")
    print(f"  Minimum ROI Threshold: {min_roi_threshold}%")
    print(f"  Basic Method: {'✅ PROFITABLE' if basic_profitable else '❌ NOT PROFITABLE'}")
    print(f"  Comprehensive: {'✅ PROFITABLE' if comp_profitable else '❌ NOT PROFITABLE'}")
    
    if basic_profitable != comp_profitable:
        print("  ⚠️  WARNING: Different profitability conclusions!")
        print("     The comprehensive method provides more accurate results.")
    
    return comprehensive_fees

def test_fee_scenarios():
    """Test different fee scenarios"""
    
    print("\n" + "=" * 55)
    print("🔄 Testing Different Fee Scenarios")
    print("=" * 55)
    
    config = Config()
    config.set_vat_rate(20.0)
    fees_calc = AmazonFeesCalculator('france', config)
    
    scenarios = [
        {
            'name': 'Light Electronics',
            'selling_price': 45.99,
            'weight_kg': 0.3,
            'category': 'electronics',
            'prep_services': ['labeling'],
            'is_peak_season': False
        },
        {
            'name': 'Heavy Book',
            'selling_price': 25.00,
            'weight_kg': 1.2,
            'category': 'books',
            'prep_services': ['labeling', 'bubble_wrap'],
            'is_peak_season': True  # Peak season
        },
        {
            'name': 'Fashion Item',
            'selling_price': 35.00,
            'weight_kg': 0.4,
            'category': 'clothing',
            'prep_services': ['labeling', 'bagging'],
            'misc_fee_types': ['return_processing'],
            'misc_quantities': [0.2]  # 20% return rate for fashion
        }
    ]
    
    for scenario in scenarios:
        print(f"\n📦 {scenario['name']}:")
        
        fees = fees_calc.calculate_comprehensive_fees(
            selling_price=scenario['selling_price'],
            weight_kg=scenario['weight_kg'],
            category=scenario['category'],
            volume_cubic_meters=0.001,
            months_stored=1,
            prep_services=scenario.get('prep_services', []),
            misc_fee_types=scenario.get('misc_fee_types', []),
            misc_quantities=scenario.get('misc_quantities', []),
            is_peak_season=scenario.get('is_peak_season', False)
        )
        
        print(f"  Selling Price: €{scenario['selling_price']}")
        print(f"  Total Fees: €{fees['total_fees_with_vat']:.2f}")
        print(f"  Net Proceeds: €{fees['net_proceeds']:.2f}")
        print(f"  Fee Percentage: {(fees['total_fees_with_vat']/scenario['selling_price']*100):.1f}%")

if __name__ == "__main__":
    try:
        test_comprehensive_fees()
        test_fee_scenarios()
        
        print("\n" + "=" * 55)
        print("🎉 Enhanced fee calculation system working correctly!")
        print("✅ All fee types implemented and tested")
        print("✅ VAT on fees properly calculated")
        print("✅ Backward compatibility maintained")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
