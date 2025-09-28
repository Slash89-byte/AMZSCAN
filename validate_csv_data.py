"""
Validate our calculations against the real Keepa CSV data
"""

import csv
from core.amazon_fees import AmazonFeesCalculator
from core.roi_calculator import ROICalculator

def parse_keepa_csv():
    """Parse the Product_viewer.csv file and extract key data"""
    
    with open('Product_viewer.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        row = next(reader)  # Get first data row
        
        # Extract key data
        asin = row['ASIN']
        title = row['Title']
        
        # Price data - try multiple sources
        current_price_str = row.get('Amazon: Current', row.get('New: Current', '€ 0'))
        current_price = float(current_price_str.replace('€ ', '').replace(',', '.'))
        
        # Weight in grams, convert to kg
        weight_g = int(row['Package: Weight (g)'])
        weight_kg = weight_g / 1000.0
        
        # Fees from Keepa
        keepa_referral_fee_pct = float(row['Referral Fee %'].replace(' %', ''))
        keepa_fba_fee_str = row['FBA Pick&Pack Fee']
        keepa_fba_fee = float(keepa_fba_fee_str.replace('€ ', '').replace(',', '.'))
        
        return {
            'asin': asin,
            'title': title,
            'current_price': current_price,
            'weight_kg': weight_kg,
            'keepa_referral_fee_pct': keepa_referral_fee_pct,
            'keepa_fba_fee': keepa_fba_fee
        }

def validate_calculations():
    """Compare our calculations with Keepa's data"""
    
    print("🔍 Validating Calculations Against Real Keepa Data")
    print("=" * 60)
    
    # Parse CSV data
    data = parse_keepa_csv()
    
    print(f"📦 ASIN: {data['asin']}")
    print(f"📝 Title: {data['title'][:60]}...")
    print(f"💰 Current Price: €{data['current_price']}")
    print(f"⚖️  Weight: {data['weight_kg']:.3f}kg ({data['weight_kg'] * 1000:.0f}g)")
    
    print("\n" + "=" * 60)
    print("📊 FEE COMPARISON")
    print("=" * 60)
    
    # Calculate fees using our system (use 'beauty' category)
    fees_calc = AmazonFeesCalculator('france')
    our_total_fees = fees_calc.calculate_fees(data['current_price'], data['weight_kg'], 'beauty')
    our_referral_fee = fees_calc.calculate_referral_fee(data['current_price'], 'beauty')
    our_fba_fee = fees_calc.calculate_fba_fee(data['weight_kg'])
    
    print(f"🏷️  Referral Fee:")
    print(f"   Keepa: {data['keepa_referral_fee_pct']:.2f}%")
    print(f"   Our calculation: {our_referral_fee / data['current_price'] * 100:.2f}%")
    print(f"   Keepa amount: €{data['current_price'] * data['keepa_referral_fee_pct'] / 100:.2f}")
    print(f"   Our amount: €{our_referral_fee:.2f}")
    
    print(f"\n📦 FBA Fee:")
    print(f"   Keepa: €{data['keepa_fba_fee']:.2f}")
    print(f"   Our calculation: €{our_fba_fee:.2f}")
    
    print(f"\n💰 Total Fees:")
    keepa_total = data['current_price'] * data['keepa_referral_fee_pct'] / 100 + data['keepa_fba_fee']
    print(f"   Keepa total: €{keepa_total:.2f}")
    print(f"   Our total: €{our_total_fees:.2f}")
    print(f"   Difference: €{abs(keepa_total - our_total_fees):.2f}")
    
    print("\n" + "=" * 60)
    print("💼 ROI ANALYSIS")
    print("=" * 60)
    
    # Test different cost prices
    test_costs = [2.00, 3.00, 3.50, 4.00]
    
    roi_calc = ROICalculator()
    
    for cost_price in test_costs:
        net_profit = data['current_price'] - our_total_fees - cost_price
        roi_result = roi_calc.calculate_roi(cost_price, data['current_price'], our_total_fees)
        roi_pct = roi_result['roi_percentage']
        grade = roi_calc.get_profitability_grade(roi_pct)
        
        profitable = "✅ PROFITABLE" if roi_pct >= 15 else "❌ NOT PROFITABLE"
        
        print(f"\n💰 Cost Price: €{cost_price:.2f}")
        print(f"   Net Profit: €{net_profit:.2f}")
        print(f"   ROI: {roi_pct:.1f}% (Grade: {grade})")
        print(f"   Status: {profitable}")

if __name__ == "__main__":
    validate_calculations()
