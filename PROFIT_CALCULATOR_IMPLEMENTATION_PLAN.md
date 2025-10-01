# Enhanced Profit Calculator - Implementation Plan

## 📋 **Overview**
Based on your responses in the questions document, this implementation plan outlines the complete redesign of the Amazon fees calculator to include all major fee types for accurate profitability analysis.

---

## 🎯 **Implementation Strategy**

### **Approach**: Complete Redesign (Option C)
- Replace existing fee calculation with comprehensive system
- All new fees default to 0 (backward compatibility)
- Single comprehensive mode (no simple/advanced split)
- Maintain existing method signatures for seamless integration

---

## 📊 **Fee Structure Implementation**

### **1. Storage Fees** 🏪
**Status**: Requires research + Keepa integration investigation

#### **Implementation Steps**:
1. **Research Amazon France storage rates** (official documentation)
2. **Investigate Keepa API** for product dimensions/volume data
3. **Default Configuration**:
   - Storage duration: 3 months (global default)
   - No seasonal variation initially
   - Alert users when dimensions unavailable

#### **Data Structure**:
```python
storage_fees = {
    'standard_size': {
        'rate_per_cubic_meter': 26.00,  # €/m³ (to be verified)
        'default_months': 3
    },
    'oversize': {
        'rate_per_cubic_meter': 18.60,  # €/m³ (to be verified)
        'default_months': 3
    }
}
```

#### **Calculation Logic**:
```python
def calculate_storage_fee(volume_m3, months=3, is_oversize=False):
    if volume_m3 is None:
        return 0.0, "Dimensions not available"
    rate = storage_rates['oversize' if is_oversize else 'standard_size']['rate_per_cubic_meter']
    return volume_m3 * rate * months, None
```

---

### **2. Prep Fees** 🏷️
**Status**: Ready to implement

#### **Implementation**:
- **Configurable per analysis** (not default services)
- **GUI Integration**: Input field in analysis dialog
- **Default**: €0.00
- **User Control**: Manual entry per product analysis

#### **Data Structure**:
```python
# Simple per-item prep fee
prep_fee_per_item = 0.0  # Default, user configurable
```

---

### **3. Inbound Shipping** 📦
**Status**: Ready to implement

#### **Implementation**:
- **Configurable cost per item** approach
- **Distributed across products** in shipment
- **GUI Integration**: Global setting + per-analysis override
- **Default**: €0.00

#### **Configuration Options**:
```python
inbound_shipping = {
    'cost_per_item': 0.0,  # Default, user configurable
    'global_default': True,  # Use global setting or per-analysis
}
```

---

### **4. Digital Services Fee** 💻
**Status**: Ready to implement

#### **Implementation**:
- **Configurable per analysis**
- **Default**: €0.00
- **Typical Use**: Amazon PPC advertising costs
- **Input Method**: Percentage of revenue or fixed amount

#### **Data Structure**:
```python
digital_services = {
    'advertising_fee_percentage': 0.0,  # % of selling price
    'fixed_service_fee': 0.0,          # Fixed amount per item
}
```

---

### **5. Miscellaneous Fees** 🔧
**Status**: Ready to implement

#### **Implementation**:
- **Configurable per analysis**
- **Default**: €0.00
- **Common Use**: Return processing, disposal fees
- **Input Method**: Fixed amount per item

---

### **6. VAT on Fees** 💰
**Status**: Critical implementation

#### **Implementation Requirements**:
1. **Calculate VAT on all Amazon fees** (referral, FBA, storage, etc.)
2. **Remove VAT from total costs** when VAT is retrieved
3. **Use configured VAT rate** (20% default)
4. **Apply to fee total**, not individual fees

#### **VAT Logic**:
```python
def apply_vat_to_fees(total_fees_before_vat, vat_rate):
    vat_on_fees = total_fees_before_vat * (vat_rate / 100)
    return total_fees_before_vat + vat_on_fees

def remove_vat_from_costs(cost_with_vat, vat_rate):
    return cost_with_vat / (1 + vat_rate / 100)
```

---

## 🏗️ **Technical Implementation Plan**

### **Phase 1: Research & Foundation** (Priority: High)

#### **Task 1.1: Storage Fee Research**
- **Research Amazon France official storage rates**
- **Verify current pricing structure**
- **Document seasonal variations**
- **Create rate validation system**

#### **Task 1.2: Keepa Integration Investigation**
- **Check Keepa API response** for product dimensions
- **Identify dimension fields** (length, width, height, volume)
- **Test with sample products**
- **Create dimension extraction methods**

#### **Task 1.3: Fee Structure Design**
- **Design comprehensive fee calculation class**
- **Define configuration schema**
- **Plan backward compatibility**

---

### **Phase 2: Core Implementation** (Priority: High)

#### **Task 2.1: Enhanced AmazonFeesCalculator**
```python
class AmazonFeesCalculator:
    def __init__(self, marketplace='france', config=None):
        # Existing code +
        self.storage_rates = {...}  # From research
        self.vat_on_fees_enabled = True
        
    def calculate_comprehensive_fees(self, 
                                   selling_price,
                                   weight_kg=0.5,
                                   category='default',
                                   dimensions=None,
                                   prep_fee=0.0,
                                   shipping_fee_per_item=0.0,
                                   digital_services_fee=0.0,
                                   misc_fee=0.0,
                                   storage_months=3):
        # Comprehensive calculation
        pass
```

#### **Task 2.2: Keepa Integration Enhancement**
```python
def extract_product_dimensions(keepa_response):
    # Extract dimensions from Keepa API response
    # Return volume in cubic meters or None
    pass
```

#### **Task 2.3: VAT Calculation System**
```python
def calculate_fees_with_vat(self, base_fees, vat_rate):
    # Apply VAT to total fees
    # Handle VAT removal from costs
    pass
```

---

### **Phase 3: GUI Integration** (Priority: Medium)

#### **Task 3.1: Enhanced Input Dialog**
- **Add new fee input fields** to product analysis
- **Prep fee input**: €0.00 default
- **Shipping cost per item**: €0.00 default  
- **Digital services fee**: €0.00 default
- **Misc fees**: €0.00 default

#### **Task 3.2: Configuration Dialog**
- **Global defaults** for new fees
- **Storage duration setting**: 3 months default
- **VAT on fees toggle**: Enabled by default

#### **Task 3.3: Results Display Enhancement**
```
Fee Breakdown:
├── Referral Fee: €X.XX
├── FBA Fee: €X.XX
├── Storage Fee: €X.XX (3 months)
├── Prep Fee: €X.XX
├── Shipping Fee: €X.XX
├── Digital Services: €X.XX
├── Misc Fees: €X.XX
├── Subtotal: €X.XX
├── VAT on Fees: €X.XX
└── Total Fees: €X.XX
```

---

### **Phase 4: Testing & Validation** (Priority: High)

#### **Task 4.1: Unit Tests**
- **Test all new fee calculations**
- **Test VAT application logic**
- **Test dimension handling**
- **Test error scenarios**

#### **Task 4.2: Integration Tests**
- **Test with real Keepa data**
- **Validate fee accuracy**
- **Test GUI integration**
- **Performance testing**

#### **Task 4.3: Real-World Validation**
- **Compare with actual Amazon fees**
- **Test with various product types**
- **Validate profitability calculations**

---

## 📋 **Data Requirements**

### **Research Tasks Before Implementation**:

1. **Amazon France Storage Rates Verification**:
   - Current €26/m³ standard rate accuracy
   - Current €18.60/m³ oversize rate accuracy
   - Peak season rate changes
   - Rate update frequency

2. **Keepa API Dimension Investigation**:
   - Available dimension fields
   - Volume calculation methods
   - Size classification criteria
   - Data availability percentage

---

## 🎯 **Implementation Priority**

### **Phase 1** (Immediate - 1-2 days):
1. ✅ Storage fee research
2. ✅ Keepa dimension investigation
3. ✅ Core fee calculation redesign

### **Phase 2** (Short-term - 2-3 days):
4. ✅ Comprehensive fee calculator implementation
5. ✅ VAT on fees system
6. ✅ Basic GUI integration

### **Phase 3** (Medium-term - 1-2 days):
7. ✅ Enhanced input/output interfaces
8. ✅ Configuration system
9. ✅ Testing and validation

---

## ⚠️ **Important Considerations**

### **Backward Compatibility**:
- All new fees default to €0.00
- Existing method signatures maintained
- Current integrations work unchanged
- Progressive enhancement approach

### **User Experience**:
- Clear fee breakdown display
- Dimension availability alerts
- Sensible defaults for all fees
- Optional fee customization

### **Accuracy**:
- Official Amazon rate verification
- Real-world validation testing
- Proper VAT calculations
- Error handling for missing data

---

## 🚀 **Next Steps**

1. **Confirm this implementation plan** meets your requirements
2. **Start with Phase 1 research tasks**:
   - Amazon France storage rates verification
   - Keepa API dimension field investigation
3. **Proceed with core implementation** once research is complete

**Are you ready to begin with the research phase, or would you like me to adjust any part of this implementation plan?**

---

*This plan provides a comprehensive roadmap for implementing accurate Amazon FBA profitability analysis with all major fee types included.*
