"""
Final end-to-end test with the real ASIN B0D8L8HYWM
"""

from core.keepa_api import KeepaAPI
from core.amazon_fees import AmazonFeesCalculator
from core.roi_calculator import ROICalculator
from utils.config import Config

def test_complete_workflow():
    """Test the complete workflow with corrected fee calculations"""
    
    print("🎯 Final End-to-End Test with Real Keepa Data")
    print("=" * 60)
    
    # Test configuration - we'll use dummy data since we don't have real API key
    test_asin = "B0D8L8HYWM"
    test_cost_price = 3.00  # Example cost price in euros
    
    # Simulate the product data based on our CSV analysis
    product_data = {
        'asin': test_asin,
        'title': 'NIVEA Lait corps Hydratation Express 72h (1 x 400 ml)',
        'current_price': 4.72,
        'sales_rank': 3793,
        'review_count': 612,
        'rating': 4.6,
        'category': 'Beauté et Parfum',
        'fee_category': 'beauty',
        'weight': 0.43,
        'in_stock': True
    }
    
    print(f"📦 Product: {test_asin}")
    print(f"📝 Title: {product_data['title']}")
    print(f"💰 Current Price: €{product_data['current_price']}")
    print(f"⚖️  Weight: {product_data['weight']}kg")
    print(f"🏷️  Category: {product_data['category']} → {product_data['fee_category']}")
    print(f"💳 Your Cost: €{test_cost_price}")
    
    # Step 1: Calculate Amazon fees with correct category
    print(f"\n1️⃣ Calculating Amazon fees for {product_data['fee_category']} category...")
    fees_calc = AmazonFeesCalculator('france')
    amazon_fees = fees_calc.calculate_fees(
        product_data['current_price'], 
        product_data['weight'], 
        product_data['fee_category']
    )
    
    referral_fee = fees_calc.calculate_referral_fee(product_data['current_price'], product_data['fee_category'])
    fba_fee = fees_calc.calculate_fba_fee(product_data['weight'])
    
    print(f"   Referral Fee: €{referral_fee:.2f} ({referral_fee/product_data['current_price']*100:.1f}%)")
    print(f"   FBA Fee: €{fba_fee:.2f}")
    print(f"   Total Fees: €{amazon_fees:.2f}")
    
    # Step 2: Calculate ROI
    print(f"\n2️⃣ Calculating ROI and profitability...")
    roi_calc = ROICalculator()
    roi_result = roi_calc.calculate_roi(
        cost_price=test_cost_price,
        selling_price=product_data['current_price'],
        amazon_fees=amazon_fees
    )
    
    roi_pct = roi_result['roi_percentage']
    net_profit = roi_result['profit']
    grade = roi_calc.get_profitability_grade(roi_pct)
    
    print(f"   Net Profit: €{net_profit:.2f}")
    print(f"   ROI: {roi_pct:.1f}%")
    print(f"   Grade: {grade}")
    
    # Step 3: Profitability assessment
    print(f"\n3️⃣ Profitability Assessment...")
    is_profitable = roi_calc.is_profitable(roi_pct, min_roi_threshold=15.0)
    
    if is_profitable:
        status = "✅ PROFITABLE"
        recommendation = "This product meets your profitability threshold!"
    else:
        status = "❌ NOT PROFITABLE"
        recommendation = "This product does not meet your 15% ROI threshold."
    
    print(f"   Status: {status}")
    print(f"   Recommendation: {recommendation}")
    
    # Step 4: Breakeven analysis
    print(f"\n4️⃣ Breakeven Analysis...")
    breakeven_price = roi_calc.calculate_breakeven_price(test_cost_price, amazon_fees, 15.0)
    
    if breakeven_price > 0:
        print(f"   For 15% ROI, you'd need selling price: €{breakeven_price:.2f}")
        print(f"   Current price vs needed: €{product_data['current_price']:.2f} vs €{breakeven_price:.2f}")
        
        if product_data['current_price'] >= breakeven_price:
            print(f"   ✅ Current price supports your ROI target")
        else:
            shortfall = breakeven_price - product_data['current_price']
            print(f"   ❌ Price is €{shortfall:.2f} too low for target ROI")
    
    print(f"\n" + "=" * 60)
    print("🎯 SUMMARY")
    print("=" * 60)
    print(f"Product: {product_data['title'][:40]}...")
    print(f"Selling Price: €{product_data['current_price']} | Cost: €{test_cost_price} | Fees: €{amazon_fees:.2f}")
    print(f"Net Profit: €{net_profit:.2f} | ROI: {roi_pct:.1f}% | Grade: {grade}")
    print(f"Verdict: {status}")
    
    return {
        'product_data': product_data,
        'fees': amazon_fees,
        'roi': roi_pct,
        'profit': net_profit,
        'profitable': is_profitable,
        'grade': grade
    }

if __name__ == "__main__":
    result = test_complete_workflow()
    print(f"\n🏁 Test completed successfully!")
