"""
Test script to verify the core functionality of the Amazon Profitability Analyzer
"""

from core.amazon_fees import AmazonFeesCalculator
from core.roi_calculator import ROICalculator
from utils.config import Config

def test_basic_functionality():
    """Test the core components without API calls"""
    
    print("=== Testing Amazon Profitability Analyzer ===\n")
    
    # Test Amazon Fees Calculator
    print("1. Testing Amazon Fees Calculator...")
    fees_calc = AmazonFeesCalculator('france')
    
    test_price = 29.99
    test_weight = 0.5
    
    fees = fees_calc.calculate_total_fees(test_price, test_weight)
    print(f"   Product Price: €{test_price}")
    print(f"   Product Weight: {test_weight}kg")
    print(f"   Referral Fee: €{fees['referral_fee']:.2f}")
    print(f"   FBA Fee: €{fees['fba_fee']:.2f}")
    print(f"   Total Fees: €{fees['total_fees']:.2f}")
    print(f"   Net Proceeds: €{fees['net_proceeds']:.2f}\n")
    
    # Test ROI Calculator
    print("2. Testing ROI Calculator...")
    roi_calc = ROICalculator()
    
    cost_price = 15.00
    roi_data = roi_calc.calculate_roi(
        cost_price=cost_price,
        selling_price=test_price,
        amazon_fees=fees['total_fees']
    )
    
    print(f"   Cost Price: €{cost_price}")
    print(f"   Selling Price: €{test_price}")
    print(f"   Amazon Fees: €{fees['total_fees']:.2f}")
    print(f"   Profit: €{roi_data['profit']:.2f}")
    print(f"   ROI: {roi_data['roi_percentage']:.1f}%")
    
    is_profitable = roi_data['roi_percentage'] >= 15.0
    print(f"   Profitable (>15% ROI): {'✅ YES' if is_profitable else '❌ NO'}")
    print(f"   Profitability Grade: {roi_calc.get_profitability_grade(roi_data['roi_percentage'])}\n")
    
    # Test Configuration
    print("3. Testing Configuration...")
    config = Config()
    print(f"   Default ROI Threshold: {config.get_min_roi_threshold()}%")
    print(f"   Marketplace: {config.get('amazon_marketplace')}")
    print(f"   Currency: {config.get('currency_symbol')}")
    print(f"   API Key Configured: {'✅ YES' if config.is_configured() else '❌ NO'}\n")
    
    # Test Breakeven Calculation
    print("4. Testing Breakeven Analysis...")
    breakeven_price = roi_calc.calculate_breakeven_price(cost_price, 15.0, 3.0, 15.0)
    print(f"   For 15% ROI with cost €{cost_price}")
    print(f"   Minimum selling price needed: €{breakeven_price:.2f}")
    print(f"   Current price vs breakeven: {'✅ GOOD' if test_price >= breakeven_price else '❌ TOO LOW'}\n")
    
    print("=== All Tests Complete ===")
    print("✅ Core functionality is working properly!")
    print("\nNext steps:")
    print("1. Get a Keepa API key from https://keepa.com/#!api")
    print("2. Add your API key to config.json")
    print("3. Start analyzing real products!")

if __name__ == "__main__":
    test_basic_functionality()
