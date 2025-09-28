"""
Amazon fees calculator for France marketplace
"""

from utils.config import Config

class AmazonFeesCalculator:
    """Calculate Amazon referral fees and FBA fees for France marketplace"""
    
    def __init__(self, marketplace='france', config: Config = None):
        self.marketplace = marketplace.lower()
        self.config = config or Config()
        
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
            'beauty': 8.0,  # Beauty products (matching real Keepa data)
        }
        
        # FBA fulfillment fees (updated to match real Keepa data)
        self.fba_fees = {
            'small_standard': {
                'base': 4.30,  # Updated base fee to match real data (€4.31 for 430g)
                'per_kg_over_1': 0.45
            },
            'large_standard': {
                'base': 5.50,  # Adjusted proportionally
                'per_kg_over_1': 0.65
            },
            'small_oversize': {
                'base': 8.90,  # Adjusted proportionally
                'per_kg_over_1': 0.85
            }
        }
        
        # VAT rate - now from configuration
        self.vat_rate = self.config.get_vat_rate()
    
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
    
    def apply_vat_to_cost(self, cost_price: float) -> float:
        """Apply VAT to cost price if configured"""
        if self.config.get_apply_vat_on_cost():
            return cost_price * (1 + self.vat_rate / 100)
        return cost_price
    
    def remove_vat_from_price(self, price_with_vat: float) -> float:
        """Remove VAT from a price that includes VAT"""
        return price_with_vat / (1 + self.vat_rate / 100)
    
    def add_vat_to_price(self, price_without_vat: float) -> float:
        """Add VAT to a price that excludes VAT"""
        return price_without_vat * (1 + self.vat_rate / 100)
    
    def get_base_selling_price(self, selling_price: float) -> float:
        """Get base selling price for fee calculations based on VAT settings"""
        # If we should apply VAT calculations on selling price AND 
        # Amazon prices include VAT, remove VAT for fee calculation base
        if (self.config.get_apply_vat_on_sale() and 
            self.config.get_vat_included_in_amazon_prices()):
            return self.remove_vat_from_price(selling_price)
        return selling_price
    
    def calculate_total_fees(self, selling_price, weight_kg=0.5, category='default', include_vat=None):
        """
        Calculate total Amazon fees with VAT handling
        Args:
            selling_price: Product selling price in euros
            weight_kg: Product weight in kg  
            category: Product category for referral fee calculation
            include_vat: Legacy parameter, use config settings instead
        Returns:
            Dictionary with fee breakdown
        """
        # Get base price for fee calculations (handles VAT removal if needed)
        base_price = self.get_base_selling_price(selling_price)
        
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
            'base_price_used': base_price,  # Price used for calculations
            'original_selling_price': selling_price,  # Original input price
            'vat_settings': {
                'vat_rate': self.vat_rate,
                'apply_vat_on_cost': self.config.get_apply_vat_on_cost(),
                'apply_vat_on_sale': self.config.get_apply_vat_on_sale(),
                'amazon_prices_include_vat': self.config.get_vat_included_in_amazon_prices(),
            },
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
