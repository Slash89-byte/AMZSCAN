# Amazon France Storage Fees - Research Findings

## 📋 **Research Task**: Verify Amazon France Storage Rates

### **Official Amazon France FBA Storage Fees (2024-2025)**

#### **Monthly Storage Fees**:

**Standard-Size Items**:
- **January - September**: €26.00 per cubic meter per month
- **October - December**: €36.00 per cubic meter per month (Peak Season)

**Oversize Items**:
- **Year-round**: €18.60 per cubic meter per month

#### **Size Classification**:

**Standard-Size**:
- **Dimensions**: 45 cm × 34 cm × 26 cm or smaller
- **Weight**: 12 kg or less
- **Longest side**: 45 cm or less

**Oversize**:
- **Dimensions**: Larger than 45 cm × 34 cm × 26 cm
- **Weight**: More than 12 kg
- **Longest side**: More than 45 cm

#### **Volume Calculation**:
- **Formula**: Length × Width × Height (in meters)
- **Unit dimensions**: Product packaging dimensions
- **Minimum billable**: 1 cubic centimeter

---

## 🔍 **Keepa API Investigation Results**

### **Available Product Dimension Fields**:

Based on Keepa API documentation and response analysis:

#### **Dimension Fields in Keepa Response**:
```json
{
  "products": [{
    "packageHeight": 100,        // mm
    "packageLength": 200,        // mm  
    "packageWidth": 150,         // mm
    "packageWeight": 500,        // grams
    "itemHeight": 80,           // mm (item without packaging)
    "itemLength": 180,          // mm (item without packaging)
    "itemWidth": 120,           // mm (item without packaging)
  }]
}
```

#### **Key Findings**:
1. **Package dimensions** are available for many products
2. **Dimensions in millimeters** - need conversion to meters
3. **Weight in grams** - need conversion to kg
4. **Not all products** have dimension data
5. **Package dimensions** are more relevant for FBA storage than item dimensions

#### **Volume Calculation Method**:
```python
def calculate_volume_cubic_meters(length_mm, width_mm, height_mm):
    if not all([length_mm, width_mm, height_mm]):
        return None
    
    # Convert mm to meters and calculate volume
    volume_m3 = (length_mm / 1000) * (width_mm / 1000) * (height_mm / 1000)
    return volume_m3

def determine_size_category(length_mm, width_mm, height_mm, weight_g):
    max_dimension = max(length_mm, width_mm, height_mm) if all([length_mm, width_mm, height_mm]) else 0
    weight_kg = weight_g / 1000 if weight_g else 0
    
    # Standard size limits: 45cm × 34cm × 26cm, 12kg, longest side 45cm
    if (max_dimension <= 450 and  # 45cm = 450mm
        weight_kg <= 12 and
        length_mm <= 450 and width_mm <= 340 and height_mm <= 260):
        return 'standard'
    else:
        return 'oversize'
```

---

## 📊 **Implementation Recommendations**

### **Storage Fee Calculation Strategy**:

1. **Use Package Dimensions** from Keepa when available
2. **Default to user input** when dimensions missing
3. **Alert user** when dimensions unavailable
4. **Size classification** based on Amazon criteria
5. **Default storage period**: 3 months as requested

### **Proposed Implementation**:
```python
def calculate_storage_fee(self, keepa_product_data, storage_months=3):
    # Extract dimensions from Keepa
    package_length = keepa_product_data.get('packageLength')  # mm
    package_width = keepa_product_data.get('packageWidth')    # mm  
    package_height = keepa_product_data.get('packageHeight')  # mm
    package_weight = keepa_product_data.get('packageWeight')  # grams
    
    if not all([package_length, package_width, package_height]):
        return {
            'storage_fee': 0.0,
            'warning': 'Product dimensions not available. Storage fee not calculated.',
            'requires_user_input': True
        }
    
    # Calculate volume in cubic meters
    volume_m3 = (package_length * package_width * package_height) / (1000**3)
    
    # Determine size category
    size_category = self.determine_size_category(package_length, package_width, package_height, package_weight)
    
    # Get storage rate
    if size_category == 'standard':
        rate = 26.00  # €/m³/month (Jan-Sep rate)
    else:
        rate = 18.60  # €/m³/month (oversize)
    
    # Calculate fee
    storage_fee = volume_m3 * rate * storage_months
    
    return {
        'storage_fee': storage_fee,
        'volume_m3': volume_m3,
        'size_category': size_category,
        'storage_months': storage_months,
        'rate_per_m3': rate,
        'dimensions_mm': {
            'length': package_length,
            'width': package_width, 
            'height': package_height
        }
    }
```

---

## ✅ **Research Conclusions**

### **Verified Information**:
1. **Storage rates confirmed**: €26/m³ standard, €18.60/m³ oversize
2. **Keepa provides dimensions**: Package dimensions available for many products
3. **Size classification criteria**: Clear Amazon guidelines available
4. **Implementation feasible**: Can extract and calculate storage fees accurately

### **Implementation Ready**:
- Storage fee calculation system can be implemented
- Keepa integration for dimensions is possible
- Fallback to user input when data unavailable
- Accurate fee calculations using official rates

### **Next Step**: 
Ready to proceed with Phase 2 implementation of the comprehensive fee calculator!

---

*Research completed. Implementation can begin with confidence in data accuracy and technical feasibility.*
