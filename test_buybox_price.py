"""
Test Buy Box price extraction from Keepa API
"""

from core.keepa_api import KeepaAPI
from core.amazon_fees import AmazonFeesCalculator
from core.roi_calculator import ROICalculator

def test_buybox_price_extraction():
    """Test that we extract the correct Buy Box price"""
    
    print("🔍 Testing Buy Box Price Extraction")
    print("=" * 50)
    
    # Simulate Keepa API response data structure
    # This simulates what we might get from the real API
    mock_product_data = {
        'asin': 'B0D8L8HYWM',
        'title': 'NIVEA Lait corps Hydratation Express 72h',
        'csv': {
            # csv[0] = Buy Box price history [timestamp1, price_cents1, timestamp2, price_cents2, ...]
            0: [1695648000, 472, 1695734400, 485, 1695820800, 472],  # €4.72, €4.85, €4.72
            # csv[1] = Amazon price history
            1: [1695648000, 472, 1695734400, 544, 1695820800, 472],  # €4.72, €5.44, €4.72
            # csv[2] = New price history  
            2: [1695648000, 472, 1695734400, 544, 1695820800, 472],
            # csv[3] = Sales rank
            3: [1695648000, 3793, 1695734400, 4093, 1695820800, 3793]
        },
        'categoryTree': [{'name': 'Beauté et Parfum'}],
        'packageWeight': 430,
        'reviewCount': 612,
        'rating': 46  # Keepa format: actual rating * 10
    }
    
    # Test with KeepaAPI parsing
    keepa_api = KeepaAPI("dummy_key")
    parsed_data = keepa_api._parse_product_data(mock_product_data)
    
    print(f"📦 ASIN: {parsed_data['asin']}")
    print(f"📝 Title: {parsed_data['title']}")
    print(f"💰 Current Price (Buy Box): €{parsed_data['current_price']}")
    print(f"🏷️  Category: {parsed_data['category']} → {parsed_data['fee_category']}")
    print(f"⚖️  Weight: {parsed_data['weight']}kg")
    
    # Verify this matches our expected Buy Box price
    expected_buybox_price = 4.72  # Latest price from csv[0]
    actual_price = parsed_data['current_price']
    
    if abs(actual_price - expected_buybox_price) < 0.01:
        print(f"✅ Buy Box price extraction: CORRECT (€{actual_price})")
    else:
        print(f"❌ Buy Box price extraction: WRONG")
        print(f"   Expected: €{expected_buybox_price}")
        print(f"   Got: €{actual_price}")
    
    # Test fee calculations with this price
    print(f"\n💸 Fee Calculation Test:")
    fees_calc = AmazonFeesCalculator('france')
    total_fees = fees_calc.calculate_fees(
        parsed_data['current_price'], 
        parsed_data['weight'], 
        parsed_data['fee_category']
    )
    
    referral_fee = fees_calc.calculate_referral_fee(parsed_data['current_price'], parsed_data['fee_category'])
    fba_fee = fees_calc.calculate_fba_fee(parsed_data['weight'])
    
    print(f"   Selling Price: €{parsed_data['current_price']:.2f}")
    print(f"   Referral Fee: €{referral_fee:.2f} ({referral_fee/parsed_data['current_price']*100:.1f}%)")
    print(f"   FBA Fee: €{fba_fee:.2f}")
    print(f"   Total Fees: €{total_fees:.2f}")
    
    # Test ROI calculation
    test_cost = 3.00
    roi_calc = ROICalculator()
    roi_result = roi_calc.calculate_roi(test_cost, parsed_data['current_price'], total_fees)
    
    print(f"\n📊 ROI Analysis (Cost: €{test_cost}):")
    print(f"   Net Profit: €{roi_result['profit']:.2f}")
    print(f"   ROI: {roi_result['roi_percentage']:.1f}%")
    print(f"   Grade: {roi_calc.get_profitability_grade(roi_result['roi_percentage'])}")
    
    return parsed_data

if __name__ == "__main__":
    test_buybox_price_extraction()
