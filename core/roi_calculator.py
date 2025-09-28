"""
ROI (Return on Investment) calculator for Amazon products
"""

from typing import Dict, Any
from utils.config import Config

class ROICalculator:
    """Calculate ROI and profit margins for Amazon products"""
    
    def __init__(self, config: Config = None):
        """
        Initialize ROI calculator with configuration
        
        Args:
            config: Configuration instance with VAT and business settings
        """
        self.config = config or Config()
        self.vat_settings = self.config.get('vat_settings', {})
        self.business_settings = self.config.get('business_model_settings', {})
    
    def calculate_roi(self, cost_price: float, selling_price: float, 
                     amazon_fees: float, additional_costs: float = 0.0) -> Dict[str, float]:
        """
        Calculate ROI for a product with VAT handling
        
        Args:
            cost_price: Your cost to acquire the product (may include VAT based on config)
            selling_price: Amazon selling price (gross, including VAT)
            amazon_fees: Total Amazon fees (referral + FBA + closing)
            additional_costs: Any additional costs (shipping to Amazon, prep, etc.)
        
        Returns:
            Dictionary with profit calculations
        """
        # Preserve original cost price for return value
        original_cost_price = cost_price
        
        # Apply VAT to cost if configured
        if self.config.get_apply_vat_on_cost():
            vat_rate = self.config.get_vat_rate()
            if vat_rate > 0:
                cost_price = cost_price * (1 + vat_rate / 100)
        
        # Calculate net proceeds (what you actually receive)
        net_proceeds = selling_price - amazon_fees
        
        # Calculate total costs
        total_costs = cost_price + additional_costs
        
        # Calculate profit
        profit = net_proceeds - total_costs
        
        # Calculate ROI percentage
        if total_costs > 0:
            roi_percentage = (profit / total_costs) * 100
        else:
            roi_percentage = 0.0
        
        # Calculate profit margin (profit as percentage of selling price)
        if selling_price > 0:
            profit_margin = (profit / selling_price) * 100
        else:
            profit_margin = 0.0
        
        return {
            'cost_price': original_cost_price,
            'selling_price': selling_price,
            'amazon_fees': amazon_fees,
            'additional_costs': additional_costs,
            'total_costs': total_costs,
            'net_proceeds': net_proceeds,
            'profit': profit,
            'roi_percentage': roi_percentage,
            'profit_margin': profit_margin
        }
    
    def apply_vat_to_cost(self, cost_price: float) -> float:
        """
        Apply VAT to cost price if configured
        
        Args:
            cost_price: Base cost price
            
        Returns:
            Cost price with VAT applied if configured
        """
        if self.config.get_apply_vat_on_cost():
            vat_rate = self.config.get_vat_rate()
            return cost_price * (1 + vat_rate / 100)
        return cost_price
    
    def get_net_selling_price(self, gross_selling_price: float) -> float:
        """
        Get net selling price (excluding VAT) from gross price
        
        Args:
            gross_selling_price: Selling price including VAT
            
        Returns:
            Net selling price (VAT excluded)
        """
        vat_rate = self.config.get_vat_rate()
        if vat_rate > 0:
            return gross_selling_price / (1 + vat_rate / 100)
        return gross_selling_price
    
    def calculate_roi_with_vat_details(self, cost_price: float, selling_price: float, 
                                     amazon_fees: float, additional_costs: float = 0.0) -> Dict[str, Any]:
        """
        Calculate ROI with detailed VAT breakdown
        
        Args:
            cost_price: Base cost price (before VAT)
            selling_price: Gross selling price (including VAT)
            amazon_fees: Total Amazon fees
            additional_costs: Additional costs
            
        Returns:
            Dictionary with detailed VAT and profit calculations
        """
        # VAT calculations
        vat_rate = self.config.get_vat_rate()
        apply_vat_on_cost = self.config.get_apply_vat_on_cost()
        
        cost_with_vat = self.apply_vat_to_cost(cost_price)
        net_selling_price = self.get_net_selling_price(selling_price)
        vat_amount = selling_price - net_selling_price
        
        # Standard ROI calculation with VAT-adjusted values
        roi_result = self.calculate_roi(cost_price, selling_price, amazon_fees, additional_costs)
        
        # Add VAT details
        roi_result.update({
            'vat_rate': vat_rate,
            'apply_vat_on_cost': apply_vat_on_cost,
            'cost_before_vat': cost_price,
            'cost_with_vat': cost_with_vat,
            'net_selling_price': net_selling_price,
            'gross_selling_price': selling_price,
            'vat_amount': vat_amount,
            'vat_on_cost': cost_with_vat - cost_price if apply_vat_on_cost else 0.0
        })
        
        return roi_result
    
    def is_profitable(self, roi_percentage: float, min_roi_threshold: float = 15.0) -> bool:
        """
        Check if product meets profitability threshold
        
        Args:
            roi_percentage: Calculated ROI percentage
            min_roi_threshold: Minimum ROI required for profitability
        
        Returns:
            True if profitable, False otherwise
        """
        return roi_percentage >= min_roi_threshold
    
    def calculate_breakeven_price(self, cost_price: float, amazon_fee_percentage: float = 15.0,
                                 fba_fee: float = 3.0, target_roi: float = 15.0) -> float:
        """
        Calculate the minimum selling price needed to achieve target ROI (VAT aware)
        
        Args:
            cost_price: Your cost to acquire the product (before VAT)
            amazon_fee_percentage: Amazon referral fee percentage
            fba_fee: FBA fulfillment fee
            target_roi: Desired ROI percentage
        
        Returns:
            Minimum selling price needed (gross, including VAT)
        """
        # Apply VAT to cost if configured
        effective_cost = self.apply_vat_to_cost(cost_price)
        
        # Formula: selling_price = (cost_price * (1 + target_roi/100) + fba_fee) / (1 - amazon_fee_percentage/100)
        target_multiplier = 1 + (target_roi / 100)
        fee_multiplier = 1 - (amazon_fee_percentage / 100)
        
        if fee_multiplier <= 0:
            return float('inf')  # Impossible to achieve target ROI
        
        min_selling_price = (effective_cost * target_multiplier + fba_fee) / fee_multiplier
        
        # Add VAT to get gross selling price
        vat_rate = self.config.get_vat_rate()
        if vat_rate > 0:
            min_selling_price = min_selling_price * (1 + vat_rate / 100)
        
        return max(min_selling_price, 0.0)
    
    def apply_vat_to_cost(self, cost_price: float) -> float:
        """Apply VAT to cost price if configured"""
        if self.config.get_apply_vat_on_cost():
            vat_rate = self.config.get_vat_rate()
            if vat_rate > 0:
                return cost_price * (1 + vat_rate / 100)
        return cost_price
    
    def analyze_profitability_scenarios(self, cost_price: float, selling_price: float,
                                      amazon_fees: float) -> Dict[str, Any]:
        """
        Analyze product profitability under different scenarios
        
        Args:
            cost_price: Your cost to acquire the product
            selling_price: Current Amazon selling price
            amazon_fees: Current Amazon fees
        
        Returns:
            Dictionary with various profitability scenarios
        """
        base_calculation = self.calculate_roi(cost_price, selling_price, amazon_fees)
        
        scenarios = {
            'current': base_calculation,
            'price_drops': {},
            'cost_increases': {},
            'breakeven': {}
        }
        
        # Analyze price drop scenarios
        for drop_percent in [5, 10, 15, 20]:
            new_price = selling_price * (1 - drop_percent / 100)
            new_fees = amazon_fees * (1 - drop_percent / 100)  # Fees scale with price
            scenarios['price_drops'][f'{drop_percent}%'] = self.calculate_roi(
                cost_price, new_price, new_fees
            )
        
        # Analyze cost increase scenarios
        for increase_percent in [5, 10, 15, 20]:
            new_cost = cost_price * (1 + increase_percent / 100)
            scenarios['cost_increases'][f'{increase_percent}%'] = self.calculate_roi(
                new_cost, selling_price, amazon_fees
            )
        
        # Calculate breakeven prices for different ROI targets
        for target_roi in [10, 15, 20, 25]:
            breakeven_price = self.calculate_breakeven_price(
                cost_price, 15.0, 3.0, target_roi
            )
            scenarios['breakeven'][f'{target_roi}%_roi'] = {
                'required_price': breakeven_price,
                'price_increase_needed': breakeven_price - selling_price,
                'feasible': breakeven_price <= selling_price * 1.2  # Within 20% of current price
            }
        
        return scenarios
    
    def get_profitability_grade(self, roi_percentage: float) -> str:
        """
        Get a letter grade for profitability
        
        Args:
            roi_percentage: ROI percentage
        
        Returns:
            Letter grade (A+ to F)
        """
        if roi_percentage >= 30:
            return 'A+'
        elif roi_percentage >= 25:
            return 'A'
        elif roi_percentage >= 20:
            return 'B+'
        elif roi_percentage >= 15:
            return 'B'
        elif roi_percentage >= 10:
            return 'C+'
        elif roi_percentage >= 5:
            return 'C'
        elif roi_percentage >= 0:
            return 'D'
        else:
            return 'F'
