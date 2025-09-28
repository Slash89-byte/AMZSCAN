"""
Quick test of the full profitability analysis workflow
"""

from core.keepa_api import KeepaAPI
from core.amazon_fees import AmazonFeesCalculator
from core.roi_calculator import ROICalculator
from utils.config import Config

def test_full_workflow():
    """Test the complete analysis workflow with real data"""
    
    print("🚀 Testing Full Profitability Analysis Workflow")
    print("=" * 60)
    
    # Configuration
    config = Config()
    test_asin = "B0D8L8HYWM"  # NIVEA body lotion
    test_cost_price = 8.50    # Example cost price in euros
    
    print(f"📦 Product: {test_asin}")
    print(f"💰 Your Cost: €{test_cost_price}")
    
    try:
        # Step 1: Get product data from Keepa
        print("\n1️⃣ Fetching product data from Keepa...")
        keepa_api = KeepaAPI(config.get_keepa_api_key())
        product_data = keepa_api.get_product_data(test_asin)
        
        if not product_data:
            print("❌ Failed to get product data")
            return False
        
        current_price = product_data.get('current_price', 0)
        product_title = product_data.get('title', 'Unknown')[:50]
        weight = product_data.get('weight', 0.5)
        
        print(f"✅ Product: {product_title}...")
        print(f"   Current Price: €{current_price}")
        print(f"   Weight: {weight}kg")
        
        # Step 2: Calculate Amazon fees
        print("\n2️⃣ Calculating Amazon fees...")
        fees_calc = AmazonFeesCalculator('france')
        amazon_fees = fees_calc.calculate_fees(current_price, weight)
        
        print(f"✅ Amazon Fees: €{amazon_fees:.2f}")
        
        # Step 3: Calculate ROI
        print("\n3️⃣ Calculating ROI and profitability...")
        roi_calc = ROICalculator()
        roi_data = roi_calc.calculate_roi(
            cost_price=test_cost_price,
            selling_price=current_price,
            amazon_fees=amazon_fees
        )
        
        # Step 4: Display results
        print("\n📊 PROFITABILITY ANALYSIS RESULTS")
        print("-" * 40)
        print(f"Selling Price: €{roi_data['selling_price']:>8.2f}")
        print(f"Amazon Fees:   €{roi_data['amazon_fees']:>8.2f}")
        print(f"Net Proceeds:  €{roi_data['net_proceeds']:>8.2f}")
        print(f"Your Cost:     €{roi_data['cost_price']:>8.2f}")
        print("-" * 40)
        print(f"PROFIT:        €{roi_data['profit']:>8.2f}")
        print(f"ROI:           {roi_data['roi_percentage']:>7.1f}%")
        print(f"Profit Margin: {roi_data['profit_margin']:>7.1f}%")
        
        # Step 5: Profitability decision
        is_profitable = roi_calc.is_profitable(roi_data['roi_percentage'], 15.0)
        grade = roi_calc.get_profitability_grade(roi_data['roi_percentage'])
        
        print("\n🎯 PROFITABILITY DECISION")
        print("-" * 40)
        status = "✅ PROFITABLE" if is_profitable else "❌ NOT PROFITABLE"
        print(f"Status: {status}")
        print(f"Grade:  {grade}")
        print(f"Threshold: 15% ROI minimum")
        
        # Step 6: Additional insights
        if roi_data['roi_percentage'] > 25:
            print("🌟 Excellent ROI - Highly recommended!")
        elif roi_data['roi_percentage'] > 15:
            print("👍 Good ROI - Recommended")
        elif roi_data['roi_percentage'] > 5:
            print("⚠️  Low ROI - Consider carefully")
        else:
            print("⛔ Poor ROI - Not recommended")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in workflow: {e}")
        return False

if __name__ == "__main__":
    test_full_workflow()
