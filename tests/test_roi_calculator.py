"""
Unit tests for ROI calculator module
"""

import unittest
import math
from core.roi_calculator import ROICalculator
from utils.config import Config


class TestROICalculator(unittest.TestCase):
    """Test cases for ROICalculator class"""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create test configuration
        self.config = Config()
        self.config.set_vat_rate(20.0)
        self.config.set_apply_vat_on_cost(True)
        
        self.roi_calc = ROICalculator(self.config)
        
        # Standard test scenario
        self.cost_price = 15.00
        self.selling_price = 29.99
        self.amazon_fees = 7.30
        self.additional_costs = 0.0

    def test_init(self):
        """Test ROICalculator initialization"""
        calc = ROICalculator()
        self.assertIsInstance(calc, ROICalculator)

    def test_calculate_roi_basic_scenario(self):
        """Test basic ROI calculation with standard values"""
        result = self.roi_calc.calculate_roi(
            self.cost_price, self.selling_price, self.amazon_fees, self.additional_costs
        )
        
        # Verify structure
        expected_keys = [
            'cost_price', 'selling_price', 'amazon_fees', 'additional_costs',
            'total_costs', 'net_proceeds', 'profit', 'roi_percentage', 'profit_margin'
        ]
        for key in expected_keys:
            self.assertIn(key, result)
        
        # Verify input values are preserved
        self.assertEqual(result['cost_price'], self.cost_price)
        self.assertEqual(result['selling_price'], self.selling_price)
        self.assertEqual(result['amazon_fees'], self.amazon_fees)
        self.assertEqual(result['additional_costs'], self.additional_costs)
        
        # Verify calculations
        expected_net_proceeds = self.selling_price - self.amazon_fees  # 29.99 - 7.30 = 22.69
        expected_total_costs = self.cost_price + self.additional_costs  # 15.00 + 0.0 = 15.00
        expected_profit = expected_net_proceeds - expected_total_costs  # 22.69 - 15.00 = 7.69
        expected_roi = (expected_profit / expected_total_costs) * 100  # (7.69 / 15.00) * 100 = 51.27%
        expected_margin = (expected_profit / self.selling_price) * 100  # (7.69 / 29.99) * 100 = 25.64%
        
        self.assertAlmostEqual(result['net_proceeds'], expected_net_proceeds, places=2)
        self.assertAlmostEqual(result['total_costs'], expected_total_costs, places=2)
        self.assertAlmostEqual(result['profit'], expected_profit, places=2)
        self.assertAlmostEqual(result['roi_percentage'], expected_roi, places=1)
        self.assertAlmostEqual(result['profit_margin'], expected_margin, places=1)

    def test_calculate_roi_with_additional_costs(self):
        """Test ROI calculation with additional costs"""
        additional_costs = 2.50
        result = self.roi_calc.calculate_roi(
            self.cost_price, self.selling_price, self.amazon_fees, additional_costs
        )
        
        expected_total_costs = self.cost_price + additional_costs  # 15.00 + 2.50 = 17.50
        expected_net_proceeds = self.selling_price - self.amazon_fees  # 22.69
        expected_profit = expected_net_proceeds - expected_total_costs  # 22.69 - 17.50 = 5.19
        expected_roi = (expected_profit / expected_total_costs) * 100  # (5.19 / 17.50) * 100 = 29.66%
        
        self.assertEqual(result['additional_costs'], additional_costs)
        self.assertAlmostEqual(result['total_costs'], expected_total_costs, places=2)
        self.assertAlmostEqual(result['profit'], expected_profit, places=2)
        self.assertAlmostEqual(result['roi_percentage'], expected_roi, places=1)

    def test_calculate_roi_negative_profit(self):
        """Test ROI calculation resulting in negative profit"""
        high_cost = 25.00  # Higher than net proceeds
        result = self.roi_calc.calculate_roi(high_cost, self.selling_price, self.amazon_fees)
        
        expected_net_proceeds = self.selling_price - self.amazon_fees  # 22.69
        expected_profit = expected_net_proceeds - high_cost  # 22.69 - 25.00 = -2.31
        expected_roi = (expected_profit / high_cost) * 100  # (-2.31 / 25.00) * 100 = -9.24%
        
        self.assertAlmostEqual(result['profit'], expected_profit, places=2)
        self.assertAlmostEqual(result['roi_percentage'], expected_roi, places=1)
        self.assertLess(result['roi_percentage'], 0)

    def test_calculate_roi_zero_cost(self):
        """Test ROI calculation with zero cost (edge case)"""
        result = self.roi_calc.calculate_roi(0.0, self.selling_price, self.amazon_fees)
        
        # When cost is zero, ROI should be 0 to avoid division by zero
        self.assertEqual(result['roi_percentage'], 0.0)
        self.assertEqual(result['total_costs'], 0.0)
        self.assertAlmostEqual(result['profit'], self.selling_price - self.amazon_fees, places=2)

    def test_calculate_roi_zero_selling_price(self):
        """Test ROI calculation with zero selling price (edge case)"""
        result = self.roi_calc.calculate_roi(self.cost_price, 0.0, 0.0)
        
        # When selling price is zero, profit margin should be 0 to avoid division by zero
        self.assertEqual(result['profit_margin'], 0.0)
        self.assertEqual(result['net_proceeds'], 0.0)
        self.assertEqual(result['profit'], -self.cost_price)
        self.assertEqual(result['roi_percentage'], -100.0)  # Lost 100% of investment

    def test_calculate_roi_high_fees(self):
        """Test ROI calculation with fees higher than selling price"""
        high_fees = 35.00  # Higher than selling price
        result = self.roi_calc.calculate_roi(self.cost_price, self.selling_price, high_fees)
        
        expected_net_proceeds = self.selling_price - high_fees  # 29.99 - 35.00 = -5.01
        expected_profit = expected_net_proceeds - self.cost_price  # -5.01 - 15.00 = -20.01
        
        self.assertLess(result['net_proceeds'], 0)
        self.assertLess(result['profit'], 0)
        self.assertLess(result['roi_percentage'], 0)

    def test_is_profitable_default_threshold(self):
        """Test profitability check with default 15% threshold"""
        # Profitable case (>15%)
        self.assertTrue(self.roi_calc.is_profitable(20.0))
        self.assertTrue(self.roi_calc.is_profitable(15.0))  # Exactly at threshold
        
        # Not profitable case (<15%)
        self.assertFalse(self.roi_calc.is_profitable(10.0))
        self.assertFalse(self.roi_calc.is_profitable(0.0))
        self.assertFalse(self.roi_calc.is_profitable(-5.0))

    def test_is_profitable_custom_threshold(self):
        """Test profitability check with custom threshold"""
        # 25% threshold
        self.assertTrue(self.roi_calc.is_profitable(30.0, 25.0))
        self.assertTrue(self.roi_calc.is_profitable(25.0, 25.0))  # Exactly at threshold
        self.assertFalse(self.roi_calc.is_profitable(20.0, 25.0))
        
        # 5% threshold
        self.assertTrue(self.roi_calc.is_profitable(10.0, 5.0))
        self.assertFalse(self.roi_calc.is_profitable(3.0, 5.0))

    def test_calculate_breakeven_price_basic(self):
        """Test breakeven price calculation with basic parameters"""
        cost_price = 15.00
        amazon_fee_percentage = 15.0
        fba_fee = 3.0
        target_roi = 15.0
        
        breakeven_price = self.roi_calc.calculate_breakeven_price(
            cost_price, amazon_fee_percentage, fba_fee, target_roi
        )
        
        # Verify the calculation
        # Formula: (cost * 1.15 + 3.0) / (1 - 0.15) = (17.25 + 3.0) / 0.85 = 20.25 / 0.85 ≈ 23.82
        expected_price = (cost_price * 1.15 + fba_fee) / 0.85
        
        self.assertAlmostEqual(breakeven_price, expected_price, places=2)
        self.assertGreater(breakeven_price, cost_price)

    def test_calculate_breakeven_price_different_targets(self):
        """Test breakeven price calculation with different ROI targets"""
        cost_price = 20.00
        
        # Higher ROI target should require higher selling price
        price_10_percent = self.roi_calc.calculate_breakeven_price(cost_price, target_roi=10.0)
        price_20_percent = self.roi_calc.calculate_breakeven_price(cost_price, target_roi=20.0)
        price_30_percent = self.roi_calc.calculate_breakeven_price(cost_price, target_roi=30.0)
        
        self.assertLess(price_10_percent, price_20_percent)
        self.assertLess(price_20_percent, price_30_percent)
        
        # All prices should be positive and greater than cost
        for price in [price_10_percent, price_20_percent, price_30_percent]:
            self.assertGreater(price, 0)
            self.assertGreater(price, cost_price)

    def test_calculate_breakeven_price_impossible_scenario(self):
        """Test breakeven price calculation with impossible fee scenario"""
        # 100% or higher fee rate makes it impossible to achieve any positive ROI
        impossible_price = self.roi_calc.calculate_breakeven_price(
            15.0, amazon_fee_percentage=100.0, target_roi=15.0
        )
        
        self.assertEqual(impossible_price, float('inf'))
        
        # Negative fee rate should still work
        negative_fee_price = self.roi_calc.calculate_breakeven_price(
            15.0, amazon_fee_percentage=-5.0, target_roi=15.0
        )
        self.assertIsInstance(negative_fee_price, float)
        self.assertGreater(negative_fee_price, 0)

    def test_calculate_breakeven_price_zero_cost(self):
        """Test breakeven price calculation with zero cost"""
        breakeven_price = self.roi_calc.calculate_breakeven_price(
            0.0, amazon_fee_percentage=15.0, fba_fee=3.0, target_roi=15.0
        )
        
        # With zero cost, only need to cover FBA fee and Amazon referral fee
        # (0 * 1.15 + 3.0) / 0.85 = 3.0 / 0.85 ≈ 3.53
        expected_price = 3.0 / 0.85
        self.assertAlmostEqual(breakeven_price, expected_price, places=2)

    def test_analyze_profitability_scenarios_structure(self):
        """Test that profitability scenarios analysis returns correct structure"""
        scenarios = self.roi_calc.analyze_profitability_scenarios(
            self.cost_price, self.selling_price, self.amazon_fees
        )
        
        # Verify main structure
        expected_keys = ['current', 'price_drops', 'cost_increases', 'breakeven']
        for key in expected_keys:
            self.assertIn(key, scenarios)
        
        # Verify current scenario
        self.assertIsInstance(scenarios['current'], dict)
        self.assertIn('roi_percentage', scenarios['current'])
        
        # Verify price drops scenarios
        expected_drops = ['5%', '10%', '15%', '20%']
        for drop in expected_drops:
            self.assertIn(drop, scenarios['price_drops'])
            self.assertIn('roi_percentage', scenarios['price_drops'][drop])
        
        # Verify cost increases scenarios
        expected_increases = ['5%', '10%', '15%', '20%']
        for increase in expected_increases:
            self.assertIn(increase, scenarios['cost_increases'])
        
        # Verify breakeven scenarios
        expected_targets = ['10%_roi', '15%_roi', '20%_roi', '25%_roi']
        for target in expected_targets:
            self.assertIn(target, scenarios['breakeven'])
            self.assertIn('required_price', scenarios['breakeven'][target])
            self.assertIn('feasible', scenarios['breakeven'][target])

    def test_analyze_profitability_scenarios_price_drops(self):
        """Test price drop scenario calculations"""
        scenarios = self.roi_calc.analyze_profitability_scenarios(
            self.cost_price, self.selling_price, self.amazon_fees
        )
        
        current_roi = scenarios['current']['roi_percentage']
        
        # ROI should decrease as price drops
        drop_5_roi = scenarios['price_drops']['5%']['roi_percentage']
        drop_10_roi = scenarios['price_drops']['10%']['roi_percentage']
        drop_20_roi = scenarios['price_drops']['20%']['roi_percentage']
        
        self.assertGreater(current_roi, drop_5_roi)
        self.assertGreater(drop_5_roi, drop_10_roi)
        self.assertGreater(drop_10_roi, drop_20_roi)

    def test_analyze_profitability_scenarios_cost_increases(self):
        """Test cost increase scenario calculations"""
        scenarios = self.roi_calc.analyze_profitability_scenarios(
            self.cost_price, self.selling_price, self.amazon_fees
        )
        
        current_roi = scenarios['current']['roi_percentage']
        
        # ROI should decrease as costs increase
        increase_5_roi = scenarios['cost_increases']['5%']['roi_percentage']
        increase_10_roi = scenarios['cost_increases']['10%']['roi_percentage']
        increase_20_roi = scenarios['cost_increases']['20%']['roi_percentage']
        
        self.assertGreater(current_roi, increase_5_roi)
        self.assertGreater(increase_5_roi, increase_10_roi)
        self.assertGreater(increase_10_roi, increase_20_roi)

    def test_analyze_profitability_scenarios_breakeven_targets(self):
        """Test breakeven price targets in scenarios"""
        scenarios = self.roi_calc.analyze_profitability_scenarios(
            self.cost_price, self.selling_price, self.amazon_fees
        )
        
        # Higher ROI targets should require higher prices
        price_10 = scenarios['breakeven']['10%_roi']['required_price']
        price_15 = scenarios['breakeven']['15%_roi']['required_price']
        price_20 = scenarios['breakeven']['20%_roi']['required_price']
        price_25 = scenarios['breakeven']['25%_roi']['required_price']
        
        self.assertLess(price_10, price_15)
        self.assertLess(price_15, price_20)
        self.assertLess(price_20, price_25)
        
        # Price increase needed should be calculated correctly
        for roi_target in ['10%_roi', '15%_roi', '20%_roi', '25%_roi']:
            required_price = scenarios['breakeven'][roi_target]['required_price']
            increase_needed = scenarios['breakeven'][roi_target]['price_increase_needed']
            expected_increase = required_price - self.selling_price
            
            self.assertAlmostEqual(increase_needed, expected_increase, places=2)

    def test_get_profitability_grade_all_ranges(self):
        """Test profitability grading for all ROI ranges"""
        test_cases = [
            (35.0, 'A+'),   # >= 30%
            (30.0, 'A+'),   # >= 30%
            (28.0, 'A'),    # >= 25%
            (25.0, 'A'),    # >= 25%
            (22.0, 'B+'),   # >= 20%
            (20.0, 'B+'),   # >= 20%
            (17.0, 'B'),    # >= 15%
            (15.0, 'B'),    # >= 15%
            (12.0, 'C+'),   # >= 10%
            (10.0, 'C+'),   # >= 10%
            (7.0, 'C'),     # >= 5%
            (5.0, 'C'),     # >= 5%
            (3.0, 'D'),     # >= 0%
            (0.0, 'D'),     # >= 0%
            (-5.0, 'F'),    # < 0%
            (-10.0, 'F')    # < 0%
        ]
        
        for roi_percentage, expected_grade in test_cases:
            actual_grade = self.roi_calc.get_profitability_grade(roi_percentage)
            self.assertEqual(actual_grade, expected_grade, 
                           f"ROI {roi_percentage}% should be grade {expected_grade}, got {actual_grade}")

    def test_get_profitability_grade_boundary_conditions(self):
        """Test profitability grading at exact boundaries"""
        boundary_tests = [
            (29.99, 'A'),   # Just below A+
            (24.99, 'B+'),  # Just below A
            (19.99, 'B'),   # Just below B+
            (14.99, 'C+'),  # Just below B
            (9.99, 'C'),    # Just below C+
            (4.99, 'D'),    # Just below C
            (-0.01, 'F')    # Just below D
        ]
        
        for roi_percentage, expected_grade in boundary_tests:
            actual_grade = self.roi_calc.get_profitability_grade(roi_percentage)
            self.assertEqual(actual_grade, expected_grade, 
                           f"ROI {roi_percentage}% should be grade {expected_grade}, got {actual_grade}")

    def test_integration_realistic_scenarios(self):
        """Test integration with realistic Amazon product scenarios"""
        # Scenario 1: Highly profitable product
        profitable_result = self.roi_calc.calculate_roi(10.0, 25.0, 5.0)
        self.assertGreater(profitable_result['roi_percentage'], 15.0)
        self.assertTrue(self.roi_calc.is_profitable(profitable_result['roi_percentage']))
        self.assertIn(self.roi_calc.get_profitability_grade(profitable_result['roi_percentage']), 
                     ['A+', 'A', 'B+', 'B'])
        
        # Scenario 2: Barely profitable product
        marginal_result = self.roi_calc.calculate_roi(18.0, 25.0, 4.0)
        roi = marginal_result['roi_percentage']
        self.assertGreater(roi, 10.0)
        self.assertLess(roi, 20.0)
        
        # Scenario 3: Loss-making product
        loss_result = self.roi_calc.calculate_roi(20.0, 25.0, 8.0)
        self.assertLess(loss_result['roi_percentage'], 0)
        self.assertFalse(self.roi_calc.is_profitable(loss_result['roi_percentage']))
        self.assertEqual(self.roi_calc.get_profitability_grade(loss_result['roi_percentage']), 'F')

    def test_precision_and_mathematical_accuracy(self):
        """Test that calculations maintain mathematical accuracy"""
        # Test with precise decimal values
        result = self.roi_calc.calculate_roi(12.99, 29.97, 7.45, 1.23)
        
        # Verify manual calculations
        expected_net_proceeds = 29.97 - 7.45  # 22.52
        expected_total_costs = 12.99 + 1.23   # 14.22
        expected_profit = 22.52 - 14.22       # 8.30
        expected_roi = (8.30 / 14.22) * 100   # 58.37%
        
        self.assertAlmostEqual(result['net_proceeds'], expected_net_proceeds, places=2)
        self.assertAlmostEqual(result['total_costs'], expected_total_costs, places=2)
        self.assertAlmostEqual(result['profit'], expected_profit, places=2)
        self.assertAlmostEqual(result['roi_percentage'], expected_roi, places=1)
        
        # Verify internal consistency
        calculated_profit = result['net_proceeds'] - result['total_costs']
        self.assertAlmostEqual(result['profit'], calculated_profit, places=10)

    def test_vat_integration_with_roi_calculation(self):
        """Test VAT integration in ROI calculations"""
        cost_price = 10.0
        selling_price = 30.0
        amazon_fees = 5.0
        
        # Test with VAT on cost enabled
        config_vat = Config()
        config_vat.set_vat_rate(20.0)
        config_vat.set_apply_vat_on_cost(True)
        
        roi_calc_with_vat = ROICalculator(config_vat)
        result_with_vat = roi_calc_with_vat.calculate_roi(cost_price, selling_price, amazon_fees)
        
        # Test without VAT on cost
        config_no_vat = Config()
        config_no_vat.set_apply_vat_on_cost(False)
        
        roi_calc_no_vat = ROICalculator(config_no_vat)
        result_no_vat = roi_calc_no_vat.calculate_roi(cost_price, selling_price, amazon_fees)
        
        # With VAT, total costs should be higher, ROI should be lower
        self.assertGreater(result_with_vat['total_costs'], result_no_vat['total_costs'])
        self.assertLess(result_with_vat['roi_percentage'], result_no_vat['roi_percentage'])
        
        # Verify VAT calculation (10 * 1.20 = 12)
        expected_vat_cost = cost_price * 1.20
        self.assertAlmostEqual(result_with_vat['cost_price'], expected_vat_cost, places=2)
    
    def test_apply_vat_to_cost_method(self):
        """Test VAT application to cost prices"""
        cost_price = 100.0
        
        # Test with VAT enabled
        vat_cost = self.roi_calc.apply_vat_to_cost(cost_price)
        expected_cost = cost_price * 1.20  # 20% VAT
        self.assertAlmostEqual(vat_cost, expected_cost, places=2)
        
        # Test with VAT disabled
        config_no_vat = Config()
        config_no_vat.set_apply_vat_on_cost(False)
        roi_calc_no_vat = ROICalculator(config_no_vat)
        
        no_vat_cost = roi_calc_no_vat.apply_vat_to_cost(cost_price)
        self.assertEqual(no_vat_cost, cost_price)
    
    def test_breakeven_calculation_with_vat(self):
        """Test breakeven price calculation considering VAT"""
        cost_price = 50.0
        target_roi = 20.0
        amazon_fee_percentage = 15.0
        fba_fee = 3.0
        
        # Calculate breakeven with VAT configuration
        breakeven_price = self.roi_calc.calculate_breakeven_price(
            cost_price, amazon_fee_percentage, fba_fee, target_roi
        )
        
        # Breakeven should be higher when VAT is applied to costs
        self.assertGreater(breakeven_price, cost_price)
        
        # Test without VAT for comparison
        config_no_vat = Config()
        config_no_vat.set_apply_vat_on_cost(False)
        roi_calc_no_vat = ROICalculator(config_no_vat)
        
        breakeven_no_vat = roi_calc_no_vat.calculate_breakeven_price(
            cost_price, amazon_fee_percentage, fba_fee, target_roi
        )
        
        # Breakeven with VAT should be higher
        self.assertGreater(breakeven_price, breakeven_no_vat)
    
    def test_different_vat_rates(self):
        """Test ROI calculations with different VAT rates"""
        cost_price = 20.0
        selling_price = 50.0
        amazon_fees = 8.0
        
        vat_rates = [0.0, 10.0, 19.0, 20.0, 22.0, 25.0]
        previous_roi = None
        
        for vat_rate in vat_rates:
            config = Config()
            config.set_vat_rate(vat_rate)
            config.set_apply_vat_on_cost(True)
            
            roi_calc = ROICalculator(config)
            result = roi_calc.calculate_roi(cost_price, selling_price, amazon_fees)
            
            # Higher VAT rates should result in lower ROI
            if previous_roi is not None:
                self.assertLessEqual(result['roi_percentage'], previous_roi)
            
            previous_roi = result['roi_percentage']
            
            # Cost price should reflect VAT
            expected_cost = cost_price * (1 + vat_rate / 100)
            self.assertAlmostEqual(result['cost_price'], expected_cost, places=2)
    
    def test_profitability_scenarios_with_vat(self):
        """Test profitability analysis scenarios with VAT considerations"""
        cost_price = 30.0
        selling_price = 80.0
        amazon_fees = 12.0
        
        scenarios = self.roi_calc.analyze_profitability_scenarios(
            cost_price, selling_price, amazon_fees
        )
        
        # Verify structure includes VAT-adjusted calculations
        self.assertIn('current', scenarios)
        self.assertIn('price_drops', scenarios)
        self.assertIn('cost_increases', scenarios)
        self.assertIn('breakeven', scenarios)
        
        # Current scenario should reflect VAT on costs
        current = scenarios['current']
        expected_vat_cost = cost_price * 1.20
        self.assertAlmostEqual(current['cost_price'], expected_vat_cost, places=2)
        
        # Verify that cost increases scenario shows impact of VAT
        cost_increase_5 = scenarios['cost_increases']['5%']
        increased_cost = cost_price * 1.05
        expected_vat_increased = increased_cost * 1.20
        self.assertAlmostEqual(cost_increase_5['cost_price'], expected_vat_increased, places=2)
    
    def test_vat_edge_cases(self):
        """Test VAT functionality edge cases"""
        # Test with zero VAT rate
        config_zero_vat = Config()
        config_zero_vat.set_vat_rate(0.0)
        config_zero_vat.set_apply_vat_on_cost(True)
        
        roi_calc_zero = ROICalculator(config_zero_vat)
        result_zero = roi_calc_zero.calculate_roi(10.0, 30.0, 5.0)
        
        # With 0% VAT, cost should remain unchanged
        self.assertEqual(result_zero['cost_price'], 10.0)
        
        # Test with very high VAT rate
        config_high_vat = Config()
        config_high_vat.set_vat_rate(50.0)
        config_high_vat.set_apply_vat_on_cost(True)
        
        roi_calc_high = ROICalculator(config_high_vat)
        result_high = roi_calc_high.calculate_roi(10.0, 30.0, 5.0)
        
        # With 50% VAT, cost should be 15.0
        self.assertAlmostEqual(result_high['cost_price'], 15.0, places=2)
        
        # ROI should be significantly lower
        self.assertLess(result_high['roi_percentage'], result_zero['roi_percentage'])


if __name__ == '__main__':
    # Run tests with detailed output
    unittest.main(verbosity=2)
