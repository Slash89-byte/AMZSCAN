"""
Enhanced ROI calculator with comprehensive Amazon fees integration
"""

from typing import Dict, Any, Tuple, Optional
from utils.config import Config
from core.enhanced_amazon_fees import EnhancedAmazonFeesCalculator

class EnhancedROICalculator:
    """Enhanced ROI calculator with comprehensive Amazon fees support"""
    
    def __init__(self, config: Config = None):
        """
        Initialize enhanced ROI calculator
        
        Args:
            config: Configuration instance with VAT and business settings
        """
        self.config = config or Config()
        self.fees_calculator = EnhancedAmazonFeesCalculator(config=self.config)
    
    def calculate_comprehensive_roi(self, 
                                  cost_price: float,
                                  selling_price: float,
                                  weight_kg: float = 0.5,
                                  category: str = 'default',
                                  keepa_data: Optional[Dict[str, Any]] = None,
                                  dimensions_mm: Optional[Tuple[int, int, int]] = None,
                                  additional_costs: float = 0.0) -> Dict[str, Any]:
        """
        Calculate comprehensive ROI with all Amazon fees included
        
        Args:
            cost_price: Your cost to acquire the product (may include VAT based on config)
            selling_price: Amazon selling price (gross, including VAT)
            weight_kg: Product weight in kg
            category: Product category for referral fee calculation
            keepa_data: Raw Keepa product data for dimensions
            dimensions_mm: Manual dimensions if Keepa data unavailable
            additional_costs: Any additional costs (shipping to Amazon, prep, etc.)
        
        Returns:
            Dictionary with comprehensive profit calculations
        """
        # Preserve original values
        original_cost_price = cost_price
        original_selling_price = selling_price
        
        # Handle VAT on cost price
        if self.config.get_apply_vat_on_cost():
            # Cost price provided already includes VAT - need to extract base cost
            vat_rate = self.config.get_vat_rate()
            base_cost_price = cost_price / (1 + vat_rate / 100)
            cost_including_vat = cost_price
        else:
            # Cost price doesn't include VAT
            base_cost_price = cost_price
            cost_including_vat = cost_price
        
        # Calculate comprehensive Amazon fees
        fees_result = self.fees_calculator.calculate_comprehensive_fees(
            selling_price=selling_price,
            weight_kg=weight_kg,
            category=category,
            keepa_data=keepa_data,
            dimensions_mm=dimensions_mm
        )
        
        # Extract fee components
        total_amazon_fees = fees_result['total_fees']
        base_price_used = fees_result['base_price_used']
        
        # Calculate net proceeds (what you actually receive after Amazon fees)
        net_proceeds = base_price_used - total_amazon_fees
        
        # Apply VAT to net proceeds if selling price includes VAT
        if (self.config.get_apply_vat_on_sale() and 
            self.config.get_vat_included_in_amazon_prices()):
            # Amazon selling price includes VAT, so net proceeds are also VAT-inclusive
            # We might need to account for VAT on our proceeds depending on business setup
            pass  # Keep proceeds as-is for now
        
        # Calculate total costs
        total_costs = cost_including_vat + additional_costs
        
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
        
        # Calculate profit margin based on net proceeds
        if net_proceeds > 0:
            net_profit_margin = (profit / net_proceeds) * 100
        else:
            net_profit_margin = 0.0
        
        # Business model additional costs
        business_costs = self._calculate_business_model_costs(base_cost_price, selling_price)
        total_business_costs = total_costs + business_costs['total_additional_costs']
        business_profit = net_proceeds - total_business_costs
        
        if total_business_costs > 0:
            business_roi = (business_profit / total_business_costs) * 100
        else:
            business_roi = 0.0
        
        # Return comprehensive results
        return {
            # Original inputs
            'original_cost_price': original_cost_price,
            'original_selling_price': original_selling_price,
            'weight_kg': weight_kg,
            'category': category,
            'additional_costs': additional_costs,
            
            # Cost calculations
            'base_cost_price': base_cost_price,
            'cost_including_vat': cost_including_vat,
            'total_costs': total_costs,
            
            # Price calculations
            'base_selling_price': base_price_used,
            'net_proceeds': net_proceeds,
            
            # Amazon fees breakdown
            'amazon_fees_breakdown': fees_result,
            'total_amazon_fees': total_amazon_fees,
            
            # Profit calculations
            'profit': profit,
            'roi_percentage': roi_percentage,
            'profit_margin': profit_margin,
            'net_profit_margin': net_profit_margin,
            
            # Business model calculations
            'business_model_costs': business_costs,
            'total_business_costs': total_business_costs,
            'business_profit': business_profit,
            'business_roi': business_roi,
            
            # Configuration details
            'vat_settings': fees_result['vat_settings'],
            'calculation_notes': self._generate_calculation_notes(fees_result),
            
            # Profitability indicators
            'is_profitable': self._is_profitable(roi_percentage),
            'meets_margin_threshold': self._meets_margin_threshold(profit_margin),
            'profitability_score': self._calculate_profitability_score(roi_percentage, profit_margin, business_roi)
        }
    
    def _calculate_business_model_costs(self, base_cost: float, selling_price: float) -> Dict[str, float]:
        """Calculate additional costs based on business model settings"""
        additional_costs = self.config.get_additional_costs()
        
        # Percentage-based additional costs
        percentage_cost = base_cost * (additional_costs.get('percentage', 0.0) / 100)
        
        # Fixed costs per unit
        shipping_cost = additional_costs.get('shipping_per_unit', 0.0)
        prep_cost = additional_costs.get('prep_per_unit', 0.0)
        
        total_additional = percentage_cost + shipping_cost + prep_cost
        
        return {
            'percentage_cost': percentage_cost,
            'shipping_cost': shipping_cost,
            'prep_cost': prep_cost,
            'total_additional_costs': total_additional,
            'percentage_rate': additional_costs.get('percentage', 0.0)
        }
    
    def _generate_calculation_notes(self, fees_result: Dict[str, Any]) -> list:
        """Generate human-readable calculation notes"""
        notes = []
        
        # VAT handling notes
        vat_settings = fees_result['vat_settings']
        if vat_settings['apply_vat_on_cost']:
            notes.append("Cost price includes VAT")
        if vat_settings['apply_vat_on_sale']:
            notes.append("Selling price VAT handling applied")
        if vat_settings['amazon_prices_include_vat']:
            notes.append("Amazon prices include VAT")
        
        # Storage fee notes
        storage_details = fees_result.get('storage_details', {})
        if storage_details.get('calculation_possible'):
            notes.append(f"Storage calculated: {storage_details['storage_months']} months, "
                        f"{storage_details['size_category']} category")
        elif storage_details.get('warning'):
            notes.append(f"Storage fee: {storage_details['warning']}")
        
        # Enhanced fees notes
        fee_settings = fees_result.get('fee_settings', {})
        enabled_fees = []
        for fee_type, settings in fee_settings.items():
            if isinstance(settings, dict) and settings.get('enabled'):
                enabled_fees.append(settings.get('description', fee_type))
        
        if enabled_fees:
            notes.append(f"Additional fees enabled: {', '.join(enabled_fees)}")
        
        # VAT on fees
        if fees_result.get('vat_on_fees', 0) > 0:
            notes.append(f"VAT applied to fees: €{fees_result['vat_on_fees']:.2f}")
        
        return notes
    
    def _is_profitable(self, roi_percentage: float) -> bool:
        """Check if product meets profitability threshold"""
        min_roi = self.config.get('min_roi_threshold', 15.0)
        return roi_percentage >= min_roi
    
    def _meets_margin_threshold(self, profit_margin: float) -> bool:
        """Check if product meets profit margin threshold"""
        min_margin = self.config.get('profit_margin_threshold', 10.0)
        return profit_margin >= min_margin
    
    def _calculate_profitability_score(self, roi: float, margin: float, business_roi: float) -> float:
        """Calculate overall profitability score (0-100)"""
        # Weighted scoring: ROI 40%, Margin 30%, Business ROI 30%
        roi_score = min(roi / 50 * 40, 40)  # Cap at 50% ROI for 40 points
        margin_score = min(margin / 25 * 30, 30)  # Cap at 25% margin for 30 points
        business_score = min(business_roi / 40 * 30, 30)  # Cap at 40% business ROI for 30 points
        
        return max(0, roi_score + margin_score + business_score)
    
    def calculate_break_even_price(self, 
                                 cost_price: float,
                                 weight_kg: float = 0.5,
                                 category: str = 'default',
                                 target_roi: float = 15.0,
                                 keepa_data: Optional[Dict[str, Any]] = None,
                                 dimensions_mm: Optional[Tuple[int, int, int]] = None) -> Dict[str, Any]:
        """
        Calculate the minimum selling price needed to achieve target ROI
        
        Args:
            cost_price: Your cost to acquire the product
            weight_kg: Product weight in kg
            category: Product category
            target_roi: Target ROI percentage
            keepa_data: Raw Keepa product data
            dimensions_mm: Manual dimensions
        
        Returns:
            Dictionary with break-even analysis
        """
        # Use iterative approach to find break-even price
        # Start with a reasonable estimate
        estimated_price = cost_price * 2.5  # Start with 150% markup
        
        for iteration in range(20):  # Max 20 iterations
            roi_result = self.calculate_comprehensive_roi(
                cost_price=cost_price,
                selling_price=estimated_price,
                weight_kg=weight_kg,
                category=category,
                keepa_data=keepa_data,
                dimensions_mm=dimensions_mm
            )
            
            current_roi = roi_result['roi_percentage']
            
            # Check if we're close enough
            if abs(current_roi - target_roi) < 0.1:
                break
            
            # Adjust estimate based on current ROI
            if current_roi < target_roi:
                estimated_price *= 1.05  # Increase price by 5%
            else:
                estimated_price *= 0.98  # Decrease price by 2%
        
        return {
            'break_even_price': estimated_price,
            'target_roi': target_roi,
            'achieved_roi': current_roi,
            'iterations': iteration + 1,
            'detailed_calculation': roi_result
        }
    
    def compare_scenarios(self, 
                         base_scenario: Dict[str, Any],
                         alternative_scenarios: list) -> Dict[str, Any]:
        """
        Compare multiple pricing/cost scenarios
        
        Args:
            base_scenario: Base scenario parameters
            alternative_scenarios: List of alternative scenario parameters
        
        Returns:
            Comparison results
        """
        base_result = self.calculate_comprehensive_roi(**base_scenario)
        
        comparisons = []
        for i, scenario in enumerate(alternative_scenarios):
            result = self.calculate_comprehensive_roi(**scenario)
            
            # Calculate differences
            roi_diff = result['roi_percentage'] - base_result['roi_percentage']
            profit_diff = result['profit'] - base_result['profit']
            margin_diff = result['profit_margin'] - base_result['profit_margin']
            
            comparisons.append({
                'scenario_id': i + 1,
                'scenario_params': scenario,
                'results': result,
                'differences': {
                    'roi_difference': roi_diff,
                    'profit_difference': profit_diff,
                    'margin_difference': margin_diff
                },
                'is_better': (roi_diff > 0 and profit_diff > 0)
            })
        
        return {
            'base_scenario': {
                'params': base_scenario,
                'results': base_result
            },
            'alternatives': comparisons,
            'best_alternative': max(comparisons, key=lambda x: x['results']['profitability_score'])
        }
    
    # Backward compatibility methods
    def calculate_roi(self, cost_price: float, selling_price: float, 
                     amazon_fees: float, additional_costs: float = 0.0) -> Dict[str, float]:
        """Backward compatibility method"""
        # Simple ROI calculation without enhanced fees
        original_cost_price = cost_price
        
        # Apply VAT to cost if configured
        if self.config.get_apply_vat_on_cost():
            vat_rate = self.config.get_vat_rate()
            if vat_rate > 0:
                cost_price = cost_price * (1 + vat_rate / 100)
        
        # Calculate net proceeds and profit
        net_proceeds = selling_price - amazon_fees
        total_costs = cost_price + additional_costs
        profit = net_proceeds - total_costs
        
        # Calculate percentages
        roi_percentage = (profit / total_costs * 100) if total_costs > 0 else 0.0
        profit_margin = (profit / selling_price * 100) if selling_price > 0 else 0.0
        
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
