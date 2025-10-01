"""
Enhanced Amazon fees calculator for France marketplace
Supports comprehensive fee structure including all Amazon fee types
"""

from utils.config import Config
from typing import Dict, Any, Optional, Tuple
import math

class EnhancedAmazonFeesCalculator:
    """Enhanced Amazon fees calculator with comprehensive fee support"""
    
    def __init__(self, marketplace='france', config: Config = None):
        self.marketplace = marketplace.lower()
        self.config = config or Config()
        
        # France marketplace referral fee structure (as of 2024)
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
            'beauty': 8.0,
            'automotive': 12.0,
            'industrial': 12.0,
            'jewelry': 20.0,
            'luggage': 15.0,
            'musical_instruments': 15.0,
            'office_products': 15.0,
            'pet_supplies': 15.0,
            'software': 15.0,
            'video_games': 15.0,
            'watches': 16.0,
        }
        
        # FBA fulfillment fees (updated based on real data)
        self.fba_fees = {
            'small_standard': {
                'base': 4.30,
                'per_kg_over_1': 0.45
            },
            'large_standard': {
                'base': 5.50,
                'per_kg_over_1': 0.65
            },
            'small_oversize': {
                'base': 8.90,
                'per_kg_over_1': 0.85
            },
            'medium_oversize': {
                'base': 12.50,
                'per_kg_over_1': 1.20
            },
            'large_oversize': {
                'base': 23.90,
                'per_kg_over_1': 1.50
            },
            'special_oversize': {
                'base': 137.50,
                'per_kg_over_1': 1.50
            }
        }
        
        # Storage fees (€/cubic meter/month)
        self.storage_fees = {
            'standard_size': {
                'jan_sep': 26.00,  # January to September
                'oct_dec': 36.00   # October to December (peak season)
            },
            'oversize': {
                'year_round': 18.60
            }
        }
        
        # Amazon size classification limits
        self.size_limits = {
            'standard_size': {
                'max_dimension': 450,    # mm
                'max_weight': 12000,     # grams
                'max_length': 450,       # mm
                'max_width': 340,        # mm
                'max_height': 260        # mm
            }
        }
        
        # VAT rate from configuration
        self.vat_rate = self.config.get_vat_rate()
        
        # Additional fee settings from config (with defaults)
        self.additional_fees = self._load_additional_fee_settings()
    
    def _load_additional_fee_settings(self) -> Dict[str, Any]:
        """Load additional fee settings from configuration"""
        return {
            'prep_fee': {
                'enabled': self.config.get('enhanced_fees.prep_fee.enabled', False),
                'type': self.config.get('enhanced_fees.prep_fee.type', 'percentage'),  # 'percentage' or 'fixed'
                'value': self.config.get('enhanced_fees.prep_fee.value', 0.0),
                'description': 'FBA Prep Service Fee'
            },
            'inbound_shipping': {
                'enabled': self.config.get('enhanced_fees.inbound_shipping.enabled', False),
                'type': self.config.get('enhanced_fees.inbound_shipping.type', 'fixed'),
                'value': self.config.get('enhanced_fees.inbound_shipping.value', 0.0),
                'description': 'Inbound Shipping Fee'
            },
            'digital_services': {
                'enabled': self.config.get('enhanced_fees.digital_services.enabled', False),
                'type': self.config.get('enhanced_fees.digital_services.type', 'percentage'),
                'value': self.config.get('enhanced_fees.digital_services.value', 0.0),
                'description': 'Digital Services Tax'
            },
            'misc_fee': {
                'enabled': self.config.get('enhanced_fees.misc_fee.enabled', False),
                'type': self.config.get('enhanced_fees.misc_fee.type', 'fixed'),
                'value': self.config.get('enhanced_fees.misc_fee.value', 0.0),
                'description': 'Miscellaneous Fee'
            },
            'vat_on_fees': {
                'enabled': self.config.get('enhanced_fees.vat_on_fees.enabled', False),
                'description': 'Apply VAT to Amazon fees'
            },
            'storage_months': self.config.get('enhanced_fees.storage_months', 3)
        }
    
    def classify_product_size(self, dimensions_mm: Tuple[int, int, int], weight_g: int) -> str:
        """
        Classify product size based on Amazon criteria
        Args:
            dimensions_mm: (length, width, height) in millimeters
            weight_g: Weight in grams
        Returns:
            Size classification string
        """
        if not dimensions_mm or not all(dimensions_mm):
            # Default classification when dimensions unavailable
            return 'unknown'
        
        length, width, height = dimensions_mm
        max_dimension = max(length, width, height)
        limits = self.size_limits['standard_size']
        
        # Check if meets standard size criteria
        if (max_dimension <= limits['max_dimension'] and
            weight_g <= limits['max_weight'] and
            length <= limits['max_length'] and
            width <= limits['max_width'] and
            height <= limits['max_height']):
            return 'standard_size'
        else:
            return 'oversize'
    
    def calculate_volume_cubic_meters(self, dimensions_mm: Tuple[int, int, int]) -> float:
        """Calculate volume in cubic meters from millimeter dimensions"""
        if not dimensions_mm or not all(dimensions_mm):
            return 0.0
        
        length, width, height = dimensions_mm
        # Convert mm to meters and calculate volume
        return (length / 1000) * (width / 1000) * (height / 1000)
    
    def calculate_storage_fee(self, keepa_data: Dict[str, Any] = None, 
                            dimensions_mm: Tuple[int, int, int] = None, 
                            weight_g: int = None, 
                            storage_months: int = None) -> Dict[str, Any]:
        """
        Calculate storage fee using Keepa data or manual dimensions
        Args:
            keepa_data: Raw Keepa product data
            dimensions_mm: Manual dimensions (length, width, height) in mm
            weight_g: Manual weight in grams
            storage_months: Storage period in months
        Returns:
            Storage fee calculation details
        """
        months = storage_months or self.additional_fees['storage_months']
        
        # Extract dimensions from Keepa data if available
        if keepa_data:
            dimensions_mm = (
                keepa_data.get('packageLength'),
                keepa_data.get('packageWidth'),
                keepa_data.get('packageHeight')
            )
            weight_g = keepa_data.get('packageWeight')
        
        if not dimensions_mm or not all(dimensions_mm):
            return {
                'storage_fee': 0.0,
                'warning': 'Product dimensions not available. Storage fee not calculated.',
                'requires_user_input': True,
                'calculation_possible': False
            }
        
        # Calculate volume and classify size
        volume_m3 = self.calculate_volume_cubic_meters(dimensions_mm)
        size_category = self.classify_product_size(dimensions_mm, weight_g or 0)
        
        # Determine storage rate
        if size_category == 'standard_size':
            # Use non-peak season rate as default
            rate = self.storage_fees['standard_size']['jan_sep']
        else:
            rate = self.storage_fees['oversize']['year_round']
        
        # Calculate fee
        storage_fee = volume_m3 * rate * months
        
        return {
            'storage_fee': storage_fee,
            'volume_m3': volume_m3,
            'size_category': size_category,
            'storage_months': months,
            'rate_per_m3': rate,
            'dimensions_mm': {
                'length': dimensions_mm[0],
                'width': dimensions_mm[1],
                'height': dimensions_mm[2]
            },
            'calculation_possible': True,
            'warning': None
        }
    
    def calculate_referral_fee(self, price: float, category: str = 'default') -> float:
        """Calculate Amazon referral fee"""
        fee_percentage = self.referral_fees.get(category, self.referral_fees['default'])
        return price * (fee_percentage / 100)
    
    def calculate_fba_fee(self, weight_kg: float = 0.5, 
                         dimensions_mm: Tuple[int, int, int] = None) -> float:
        """
        Calculate FBA fulfillment fee based on size and weight
        Args:
            weight_kg: Product weight in kg
            dimensions_mm: Product dimensions in mm
        """
        # Determine size tier
        if dimensions_mm:
            weight_g = weight_kg * 1000
            size_category = self.classify_product_size(dimensions_mm, weight_g)
            
            if size_category == 'standard_size':
                if weight_kg <= 1.0:
                    tier = 'small_standard'
                else:
                    tier = 'large_standard'
            else:
                # Oversize classification
                if weight_kg <= 2.0:
                    tier = 'small_oversize'
                elif weight_kg <= 30.0:
                    tier = 'medium_oversize'
                elif weight_kg <= 70.0:
                    tier = 'large_oversize'
                else:
                    tier = 'special_oversize'
        else:
            # Fallback when no dimensions available
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
    
    def calculate_closing_fee(self, price: float) -> float:
        """Calculate variable closing fee (for media items, usually 0 for most products)"""
        return 0.0
    
    def calculate_additional_fee(self, fee_config: Dict[str, Any], 
                               base_price: float) -> float:
        """
        Calculate additional fee based on configuration
        Args:
            fee_config: Fee configuration dictionary
            base_price: Base price for percentage calculations
        """
        if not fee_config.get('enabled', False):
            return 0.0
        
        fee_type = fee_config.get('type', 'fixed')
        fee_value = fee_config.get('value', 0.0)
        
        if fee_type == 'percentage':
            return base_price * (fee_value / 100)
        else:  # fixed
            return fee_value
    
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
        # If Amazon prices include VAT, remove VAT for fee calculation base
        if (self.config.get_apply_vat_on_sale() and 
            self.config.get_vat_included_in_amazon_prices()):
            return self.remove_vat_from_price(selling_price)
        return selling_price
    
    def calculate_comprehensive_fees(self, 
                                   selling_price: float,
                                   weight_kg: float = 0.5,
                                   category: str = 'default',
                                   keepa_data: Dict[str, Any] = None,
                                   dimensions_mm: Tuple[int, int, int] = None) -> Dict[str, Any]:
        """
        Calculate comprehensive Amazon fees including all fee types
        Args:
            selling_price: Product selling price in euros
            weight_kg: Product weight in kg
            category: Product category for referral fee calculation
            keepa_data: Raw Keepa product data for dimensions
            dimensions_mm: Manual dimensions if Keepa data unavailable
        Returns:
            Comprehensive fee breakdown dictionary
        """
        # Get base price for fee calculations (handles VAT removal if needed)
        base_price = self.get_base_selling_price(selling_price)
        
        # Core Amazon fees
        referral_fee = self.calculate_referral_fee(base_price, category)
        fba_fee = self.calculate_fba_fee(weight_kg, dimensions_mm)
        closing_fee = self.calculate_closing_fee(base_price)
        
        # Storage fee calculation
        storage_result = self.calculate_storage_fee(keepa_data, dimensions_mm, 
                                                  int(weight_kg * 1000) if weight_kg else None)
        storage_fee = storage_result['storage_fee']
        
        # Additional fees
        prep_fee = self.calculate_additional_fee(self.additional_fees['prep_fee'], base_price)
        inbound_shipping = self.calculate_additional_fee(self.additional_fees['inbound_shipping'], base_price)
        digital_services = self.calculate_additional_fee(self.additional_fees['digital_services'], base_price)
        misc_fee = self.calculate_additional_fee(self.additional_fees['misc_fee'], base_price)
        
        # Total fees before VAT
        total_fees_before_vat = (referral_fee + fba_fee + closing_fee + storage_fee + 
                               prep_fee + inbound_shipping + digital_services + misc_fee)
        
        # Apply VAT to fees if enabled
        if self.additional_fees['vat_on_fees']['enabled']:
            vat_on_fees = total_fees_before_vat * (self.vat_rate / 100)
            total_fees = total_fees_before_vat + vat_on_fees
        else:
            vat_on_fees = 0.0
            total_fees = total_fees_before_vat
        
        # Calculate net proceeds
        net_proceeds = base_price - total_fees
        
        return {
            # Core fees
            'referral_fee': referral_fee,
            'fba_fee': fba_fee,
            'closing_fee': closing_fee,
            
            # Additional fees
            'storage_fee': storage_fee,
            'prep_fee': prep_fee,
            'inbound_shipping': inbound_shipping,
            'digital_services': digital_services,
            'misc_fee': misc_fee,
            
            # VAT calculations
            'vat_on_fees': vat_on_fees,
            'total_fees_before_vat': total_fees_before_vat,
            'total_fees': total_fees,
            
            # Results
            'net_proceeds': net_proceeds,
            'base_price_used': base_price,
            'original_selling_price': selling_price,
            
            # Storage calculation details
            'storage_details': storage_result,
            
            # Configuration info
            'fee_settings': self.additional_fees,
            'vat_settings': {
                'vat_rate': self.vat_rate,
                'apply_vat_on_cost': self.config.get_apply_vat_on_cost(),
                'apply_vat_on_sale': self.config.get_apply_vat_on_sale(),
                'amazon_prices_include_vat': self.config.get_vat_included_in_amazon_prices(),
            },
            
            # Breakdown details
            'fee_breakdown': {
                'referral_percentage': self.referral_fees.get(category, self.referral_fees['default']),
                'weight_kg': weight_kg,
                'category': category,
                'dimensions_used': dimensions_mm,
                'keepa_data_available': keepa_data is not None
            }
        }
    
    def calculate_total_fees(self, selling_price: float, weight_kg: float = 0.5, 
                           category: str = 'default', **kwargs) -> Dict[str, Any]:
        """
        Backward compatibility method - delegates to comprehensive calculation
        """
        return self.calculate_comprehensive_fees(selling_price, weight_kg, category, **kwargs)
    
    def calculate_fees(self, selling_price: float, weight_kg: float = 0.5, 
                      category: str = 'default') -> float:
        """Simplified method that returns just the total fees amount"""
        fees_data = self.calculate_comprehensive_fees(selling_price, weight_kg, category)
        return fees_data['total_fees']
