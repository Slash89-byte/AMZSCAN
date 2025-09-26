"""
Amazon fees calculator for France marketplace
"""

class AmazonFeesCalculator:
    """Calculate Amazon referral fees and FBA fees for France marketplace"""
    
    def __init__(self, marketplace='france'):
        self.marketplace = marketplace.lower()
        
        # France marketplace fee structure (as of 2024)
        self.referral_fees = {
            # Default referral fee categories (percentage)
            'default': 15.0,
            'electronics': 8.0,
            'computers': 6.0,
            'books': 15.0,
            'clothing': 17.0,
            'home_garden': 15.0,
            'sports': 15.0,
            'toys': 15.0,
        }
        
        # FBA fulfillment fees (simplified structure)
        self.fba_fees = {
            'small_standard': {
                'base': 2.80,  # Base fee in euros
                'per_kg_over_1': 0.45
            },
            'large_standard': {
                'base': 3.90,
                'per_kg_over_1': 0.65
            },
            'small_oversize': {
                'base': 6.90,
                'per_kg_over_1': 0.85
            }
        }
        
        # VAT rate for France
        self.vat_rate = 0.20  # 20%
    
    def calculate_referral_fee(self, price, category='default'):
        """Calculate Amazon referral fee"""
        fee_percentage = self.referral_fees.get(category, self.referral_fees['default'])
        return price * (fee_percentage / 100)
    
    def calculate_fba_fee(self, weight_kg=0.5, dimensions=None):
        """
        Calculate FBA fulfillment fee
        Args:
            weight_kg: Product weight in kg
            dimensions: Tuple of (length, width, height) in cm
        """
        # Simplified size tier determination
        # In reality, this would be more complex based on exact dimensions
        if weight_kg <= 1.0:
            tier = 'small_standard'
        elif weight_kg <= 10.0:
            tier = 'large_standard'
        else:
            tier = 'small_oversize'
        
        fee_structure = self.fba_fees[tier]
        base_fee = fee_structure['base']
        
        # Additional fee for weight over 1kg
        if weight_kg > 1.0:
            extra_weight = weight_kg - 1.0
            extra_fee = extra_weight * fee_structure['per_kg_over_1']
            return base_fee + extra_fee
        
        return base_fee
    
    def calculate_closing_fee(self, price):
        """Calculate variable closing fee (for media items, usually 0 for most products)"""
        # Most products don't have closing fees, but media items do
        return 0.0
    
    def calculate_total_fees(self, selling_price, weight_kg=0.5, category='default', include_vat=False):
        """
        Calculate total Amazon fees
        Args:
            selling_price: Product selling price in euros
            weight_kg: Product weight in kg  
            category: Product category for referral fee calculation
            include_vat: Whether to include VAT in calculations
        Returns:
            Dictionary with fee breakdown
        """
        # Base price (excluding VAT if needed)
        base_price = selling_price / (1 + self.vat_rate) if include_vat else selling_price
        
        referral_fee = self.calculate_referral_fee(base_price, category)
        fba_fee = self.calculate_fba_fee(weight_kg)
        closing_fee = self.calculate_closing_fee(base_price)
        
        total_fees = referral_fee + fba_fee + closing_fee
        
        return {
            'referral_fee': referral_fee,
            'fba_fee': fba_fee,
            'closing_fee': closing_fee,
            'total_fees': total_fees,
            'net_proceeds': base_price - total_fees,
            'fee_breakdown': {
                'referral_percentage': self.referral_fees.get(category, self.referral_fees['default']),
                'weight_kg': weight_kg,
                'category': category
            }
        }
    
    def calculate_fees(self, selling_price, weight_kg=0.5, category='default'):
        """Simplified method that returns just the total fees amount"""
        fees_data = self.calculate_total_fees(selling_price, weight_kg, category)
        return fees_data['total_fees']
