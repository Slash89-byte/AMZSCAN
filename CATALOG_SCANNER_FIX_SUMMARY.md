# Catalog Scanner Bug Fixes and Enhancements

**Date:** October 5, 2025  
**Issue:** Catalog scanner had multiple issues preventing proper functionality

## Problems Fixed

### 1. Method Name Error ❌
**Error:** `'ProductMatcher' object has no attribute 'match_product'`
- **Root Cause:** Incorrect method name used in `CatalogScanWorker.run()`
- **Fix:** Changed `match_product()` to `match_single_product()` (correct method name)

### 2. Missing Price and FBA Fee Information 💰
**Problem:** Price and FBA costs were not being displayed or calculated properly
- **Root Cause:** Basic fee estimation instead of using `EnhancedROICalculator`
- **Fix:** Integrated `EnhancedROICalculator` for accurate FBA fee calculation including:
  - FBA fulfillment fees (based on dimensions/weight)
  - Referral fees (category-specific rates)
  - Storage fees (monthly estimate)
  - Total fees breakdown

### 3. API Token Conservation 🎯
**Problem:** Testing consumed too many Keepa API tokens
- **Fix:** Added **TEST MODE** limiting scans to first 5 products
- **Location:** `CatalogScanWorker.run()` - line 189
- **Note:** Change `test_limit = 5` to process more products in production

## Code Changes

### File: `utils/product_matcher.py`

#### Enhanced MatchedProduct Dataclass
```python
@dataclass
class MatchedProduct:
    # ... existing fields ...
    # NEW: Fee breakdown fields
    fba_fee: Optional[float] = None
    referral_fee: Optional[float] = None
    storage_fee: Optional[float] = None
    total_fees: Optional[float] = None
```

#### Enhanced Profitability Calculation
```python
def _calculate_profitability(self, wholesale_price, amazon_price, keepa_data):
    """
    Now uses EnhancedROICalculator for accurate fee calculation
    
    Extracts from Keepa data:
    - Package dimensions (length, width, height in cm)
    - Package weight (kg)
    - Product category (for accurate referral fee %)
    
    Returns detailed breakdown:
    - profit_margin: Net profit after all fees
    - roi_percentage: Return on investment %
    - fba_fee: FBA fulfillment fee
    - referral_fee: Amazon referral fee (category-dependent)
    - storage_fee: Monthly storage fee estimate
    - estimated_fees: Total of all fees
    """
```

### File: `gui/catalog_scanner.py`

#### Enhanced Results Table
**Before:** 11 columns (missing fee details)  
**After:** 13 columns with full fee breakdown

New columns:
- `FBA Fee €` - FBA fulfillment fee
- `Referral Fee €` - Amazon referral/commission fee  
- `Total Fees €` - Sum of all Amazon fees

**Color Coding:**
- **Green** profit = profitable (>0)
- **Red** profit = loss (<0)
- **Green** ROI = excellent (>20%)
- **Orange** ROI = marginal (<10%)
- **Green** status = "matched"
- **Red** status = "not_found", "gtin_invalid"
- **Orange** status = other states

#### Test Mode Limiter
```python
# TESTING MODE: Limit to first 5 products to save API tokens
test_limit = 5
rows_to_process = self.catalog_data.rows[:test_limit]
```

## Testing Checklist

- [x] Fix method name error (`match_single_product`)
- [x] Add fee fields to `MatchedProduct` dataclass
- [x] Integrate `EnhancedROICalculator` for accurate fees
- [x] Update results table to 13 columns
- [x] Display FBA fee, referral fee, total fees
- [x] Store fees in matched products (both GTIN and fallback)
- [x] Add color coding for profit/ROI/status
- [x] Limit test mode to 5 products
- [ ] Test with real wholesaler catalog
- [ ] Verify fee calculations are accurate
- [ ] Confirm API token usage is reduced

## Usage Instructions

### Testing Mode (Current Default)
1. Upload your wholesaler catalog
2. **Only first 5 products will be scanned** (saves API tokens)
3. Review results including detailed fee breakdown
4. Export results to CSV

### Production Mode
To process more products, edit `gui/catalog_scanner.py` line ~189:
```python
# Change from:
test_limit = 5

# To desired number or remove limit entirely:
test_limit = 100  # or any number
# OR for unlimited:
rows_to_process = self.catalog_data.rows  # process all rows
```

## Results Table Guide

| Column | Description | Example |
|--------|-------------|---------|
| GTIN | Product barcode | 8809647393238 |
| Brand | Product brand | Dermacol |
| Product Name | Product description | Cover Foundation 208 |
| Category | Amazon category | Health & Personal Care |
| Wholesale € | Your cost price | 5.50 |
| Amazon € | Current selling price | 15.99 |
| FBA Fee € | Fulfillment fee | 3.45 |
| Referral Fee € | Amazon commission | 2.40 |
| Total Fees € | All Amazon fees | 6.35 |
| Profit € | Net profit | 4.14 (green if >0) |
| ROI % | Return on investment | 75.3% (green if >20%) |
| Status | Match status | matched, not_found, etc. |
| ASIN | Amazon product ID | B07XYZABC12 |

## Fee Calculation Details

The system now uses **EnhancedROICalculator** which considers:

### FBA Fees (Weight-based)
- Small standard: 0-500g → €2.80 - €3.50
- Large standard: 500-1000g → €3.50 - €4.50
- Large bulky: >1kg → €4.50+

### Referral Fees (Category-based)
- Health & Personal Care: 15%
- Beauty: 15%
- Electronics: 8%
- Books: 15%
- Clothing: 15%
- Default: 15%

### Storage Fees (Monthly)
- Standard size: €0.05-0.10 per cubic foot
- Based on dimensions from Keepa data
- Estimated at 30 sales/month velocity

### Calculation Formula
```
Profit = Amazon Price - Wholesale Cost - FBA Fee - Referral Fee - Storage Fee
ROI % = (Profit / Wholesale Cost) × 100
```

## Next Steps

1. **Test** the scanner with your real catalog (limited to 5 items)
2. **Verify** fee calculations match Amazon's fee calculator
3. **Adjust** test_limit if needed for larger batches
4. **Review** matched products for accuracy
5. **Export** profitable products to CSV for further analysis

## API Token Conservation Strategy

**Current Test Mode:**
- 5 products × 1-3 GTIN attempts = 5-15 API calls
- Estimated cost: 5-15 tokens (vs 100+ for full catalog)

**Best Practices:**
- Use test mode for initial validation
- Process catalogs in batches of 10-50 products
- Monitor Keepa API usage in dashboard
- Save templates for recurring wholesalers (no re-detection needed)

## Known Limitations

1. **Dimensions fallback:** If Keepa data lacks dimensions, uses estimates (20×15×10cm, 300g)
2. **Category detection:** Uses Keepa category tree; falls back to "Health & Personal Care"
3. **Price accuracy:** Based on most recent Keepa data snapshot
4. **Storage fees:** Estimated at 30 sales/month; adjust in `EnhancedROICalculator` if needed

## Support

If you encounter issues:
1. Check logs in the scan progress section
2. Verify Keepa API key is configured
3. Ensure catalog format matches expected columns
4. Review GTIN validity (8-14 digits)
5. Check internet connection for API calls
