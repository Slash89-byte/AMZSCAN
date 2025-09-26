"""
ROI (Return on Investment) calculator for Amazon products
"""

from typing import Dict, Any

class ROICalculator:
    """Calculate ROI and profit margins for Amazon products"""
    
    def __init__(self):
        pass
    
    def calculate_roi(self, cost_price: float, selling_price: float, 
                     amazon_fees: float, additional_costs: float = 0.0) -> Dict[str, float]:
        """
        Calculate ROI for a product
        
        Args:
            cost_price: Your cost to acquire the product
            selling_price: Amazon selling price
            amazon_fees: Total Amazon fees (referral + FBA + closing)
            additional_costs: Any additional costs (shipping to Amazon, prep, etc.)
        
        Returns:
            Dictionary with profit calculations
        """
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
            'cost_price': cost_price,
            'selling_price': selling_price,
            'amazon_fees': amazon_fees,
            'additional_costs': additional_costs,
            'total_costs': total_costs,
            'net_proceeds': net_proceeds,
            'profit': profit,
            'roi_percentage': roi_percentage,
            'profit_margin': profit_margin
        }
    
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
        Calculate the minimum selling price needed to achieve target ROI
        
        Args:
            cost_price: Your cost to acquire the product
            amazon_fee_percentage: Amazon referral fee percentage
            fba_fee: FBA fulfillment fee
            target_roi: Desired ROI percentage
        
        Returns:
            Minimum selling price needed
        """
        # Formula: selling_price = (cost_price * (1 + target_roi/100) + fba_fee) / (1 - amazon_fee_percentage/100)
        target_multiplier = 1 + (target_roi / 100)
        fee_multiplier = 1 - (amazon_fee_percentage / 100)
        
        if fee_multiplier <= 0:
            return float('inf')  # Impossible to achieve target ROI
        
        min_selling_price = (cost_price * target_multiplier + fba_fee) / fee_multiplier
        return max(min_selling_price, 0.0)
    
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
