"""
Unit tests for Amazon fees calculator module
"""

import unittest
from core.amazon_fees import AmazonFeesCalculator


class TestAmazonFeesCalculator(unittest.TestCase):
    """Test cases for AmazonFeesCalculator class"""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.fees_calc = AmazonFeesCalculator('france')
        self.test_price = 29.99
        self.test_weight = 0.5

    def test_init_default_marketplace(self):
        """Test initialization with default marketplace"""
        calc = AmazonFeesCalculator()
        self.assertEqual(calc.marketplace, 'france')
        self.assertEqual(calc.vat_rate, 0.20)
        self.assertIn('default', calc.referral_fees)
        self.assertIn('small_standard', calc.fba_fees)

    def test_init_custom_marketplace(self):
        """Test initialization with custom marketplace"""
        calc = AmazonFeesCalculator('FRANCE')  # Test case insensitive
        self.assertEqual(calc.marketplace, 'france')
        
        calc2 = AmazonFeesCalculator('germany')
        self.assertEqual(calc2.marketplace, 'germany')

    def test_referral_fees_structure(self):
        """Test that referral fees structure is properly initialized"""
        expected_categories = [
            'default', 'electronics', 'computers', 'books', 
            'clothing', 'home_garden', 'sports', 'toys'
        ]
        
        for category in expected_categories:
            self.assertIn(category, self.fees_calc.referral_fees)
            self.assertIsInstance(self.fees_calc.referral_fees[category], float)
            self.assertGreater(self.fees_calc.referral_fees[category], 0)

    def test_fba_fees_structure(self):
        """Test that FBA fees structure is properly initialized"""
        expected_tiers = ['small_standard', 'large_standard', 'small_oversize']
        
        for tier in expected_tiers:
            self.assertIn(tier, self.fees_calc.fba_fees)
            self.assertIn('base', self.fees_calc.fba_fees[tier])
            self.assertIn('per_kg_over_1', self.fees_calc.fba_fees[tier])
            self.assertGreater(self.fees_calc.fba_fees[tier]['base'], 0)
            self.assertGreater(self.fees_calc.fba_fees[tier]['per_kg_over_1'], 0)

    def test_calculate_referral_fee_default_category(self):
        """Test referral fee calculation with default category"""
        price = 100.0
        expected_fee = price * (self.fees_calc.referral_fees['default'] / 100)
        
        actual_fee = self.fees_calc.calculate_referral_fee(price)
        
        self.assertEqual(actual_fee, expected_fee)
        self.assertEqual(actual_fee, 15.0)  # 100 * 15% = 15

    def test_calculate_referral_fee_specific_categories(self):
        """Test referral fee calculation with specific categories"""
        price = 100.0
        
        # Test electronics category (8%)
        electronics_fee = self.fees_calc.calculate_referral_fee(price, 'electronics')
        self.assertEqual(electronics_fee, 8.0)
        
        # Test computers category (6%)
        computers_fee = self.fees_calc.calculate_referral_fee(price, 'computers')
        self.assertEqual(computers_fee, 6.0)
        
        # Test clothing category (17%)
        clothing_fee = self.fees_calc.calculate_referral_fee(price, 'clothing')
        self.assertEqual(clothing_fee, 17.0)

    def test_calculate_referral_fee_unknown_category(self):
        """Test referral fee calculation with unknown category falls back to default"""
        price = 100.0
        unknown_fee = self.fees_calc.calculate_referral_fee(price, 'unknown_category')
        default_fee = self.fees_calc.calculate_referral_fee(price, 'default')
        
        self.assertEqual(unknown_fee, default_fee)

    def test_calculate_referral_fee_zero_price(self):
        """Test referral fee calculation with zero price"""
        fee = self.fees_calc.calculate_referral_fee(0.0)
        self.assertEqual(fee, 0.0)

    def test_calculate_fba_fee_small_standard_under_1kg(self):
        """Test FBA fee calculation for small standard items under 1kg"""
        weight = 0.5
        fee = self.fees_calc.calculate_fba_fee(weight)
        expected_fee = self.fees_calc.fba_fees['small_standard']['base']
        
        self.assertEqual(fee, expected_fee)
        self.assertEqual(fee, 2.80)

    def test_calculate_fba_fee_small_standard_exactly_1kg(self):
        """Test FBA fee calculation for small standard items exactly 1kg"""
        weight = 1.0
        fee = self.fees_calc.calculate_fba_fee(weight)
        expected_fee = self.fees_calc.fba_fees['small_standard']['base']
        
        self.assertEqual(fee, expected_fee)
        self.assertEqual(fee, 2.80)

    def test_calculate_fba_fee_small_standard_over_1kg(self):
        """Test FBA fee calculation for items that would theoretically be small_standard over 1kg"""
        # Note: In the current implementation, items over 1kg go to large_standard
        # This test verifies the tier boundary logic works correctly
        weight = 1.5
        # This will be large_standard tier since weight > 1.0
        base_fee = self.fees_calc.fba_fees['large_standard']['base']  # 3.90
        extra_weight = weight - 1.0  # 0.5
        extra_fee = extra_weight * self.fees_calc.fba_fees['large_standard']['per_kg_over_1']  # 0.5 * 0.65
        expected_fee = base_fee + extra_fee  # 3.90 + 0.325 = 4.225
        
        actual_fee = self.fees_calc.calculate_fba_fee(weight)
        
        self.assertEqual(actual_fee, expected_fee)
        self.assertAlmostEqual(actual_fee, 4.225, places=3)

    def test_calculate_fba_fee_large_standard(self):
        """Test FBA fee calculation for large standard items"""
        weight = 5.0
        base_fee = self.fees_calc.fba_fees['large_standard']['base']
        extra_weight = weight - 1.0
        extra_fee = extra_weight * self.fees_calc.fba_fees['large_standard']['per_kg_over_1']
        expected_fee = base_fee + extra_fee
        
        actual_fee = self.fees_calc.calculate_fba_fee(weight)
        
        self.assertEqual(actual_fee, expected_fee)
        self.assertEqual(actual_fee, 3.90 + (4.0 * 0.65))  # 3.90 + 2.60 = 6.50

    def test_calculate_fba_fee_small_oversize(self):
        """Test FBA fee calculation for small oversize items"""
        weight = 15.0
        base_fee = self.fees_calc.fba_fees['small_oversize']['base']
        extra_weight = weight - 1.0
        extra_fee = extra_weight * self.fees_calc.fba_fees['small_oversize']['per_kg_over_1']
        expected_fee = base_fee + extra_fee
        
        actual_fee = self.fees_calc.calculate_fba_fee(weight)
        
        self.assertEqual(actual_fee, expected_fee)
        self.assertEqual(actual_fee, 6.90 + (14.0 * 0.85))  # 6.90 + 11.90 = 18.80

    def test_calculate_fba_fee_weight_boundaries(self):
        """Test FBA fee calculation at weight tier boundaries"""
        # Test boundary between small_standard and large_standard (1kg)
        fee_1kg = self.fees_calc.calculate_fba_fee(1.0)
        fee_1kg_plus = self.fees_calc.calculate_fba_fee(1.001)
        
        self.assertEqual(fee_1kg, 2.80)  # small_standard base
        self.assertGreater(fee_1kg_plus, 2.80)  # large_standard base
        
        # Test boundary between large_standard and small_oversize (10kg)
        fee_10kg = self.fees_calc.calculate_fba_fee(10.0)
        fee_10kg_plus = self.fees_calc.calculate_fba_fee(10.001)
        
        # Both should use different tier bases
        self.assertNotEqual(fee_10kg, fee_10kg_plus)

    def test_calculate_fba_fee_zero_weight(self):
        """Test FBA fee calculation with zero weight"""
        fee = self.fees_calc.calculate_fba_fee(0.0)
        expected_fee = self.fees_calc.fba_fees['small_standard']['base']
        
        self.assertEqual(fee, expected_fee)

    def test_calculate_closing_fee(self):
        """Test closing fee calculation (should be 0 for most products)"""
        fee = self.fees_calc.calculate_closing_fee(100.0)
        self.assertEqual(fee, 0.0)
        
        fee_zero = self.fees_calc.calculate_closing_fee(0.0)
        self.assertEqual(fee_zero, 0.0)

    def test_calculate_total_fees_default_parameters(self):
        """Test total fees calculation with default parameters"""
        selling_price = 29.99
        result = self.fees_calc.calculate_total_fees(selling_price)
        
        # Verify structure
        expected_keys = [
            'referral_fee', 'fba_fee', 'closing_fee', 'total_fees', 
            'net_proceeds', 'fee_breakdown'
        ]
        for key in expected_keys:
            self.assertIn(key, result)
        
        # Verify calculations
        expected_referral = selling_price * 0.15  # 15% default
        expected_fba = 2.80  # small_standard base for 0.5kg
        expected_closing = 0.0
        expected_total = expected_referral + expected_fba + expected_closing
        expected_net = selling_price - expected_total
        
        self.assertAlmostEqual(result['referral_fee'], expected_referral, places=2)
        self.assertEqual(result['fba_fee'], expected_fba)
        self.assertEqual(result['closing_fee'], expected_closing)
        self.assertAlmostEqual(result['total_fees'], expected_total, places=2)
        self.assertAlmostEqual(result['net_proceeds'], expected_net, places=2)

    def test_calculate_total_fees_with_vat(self):
        """Test total fees calculation including VAT"""
        selling_price_with_vat = 29.99
        result = self.fees_calc.calculate_total_fees(selling_price_with_vat, include_vat=True)
        
        # Base price should be calculated excluding VAT
        expected_base_price = selling_price_with_vat / (1 + self.fees_calc.vat_rate)
        expected_referral = expected_base_price * 0.15
        
        self.assertAlmostEqual(result['referral_fee'], expected_referral, places=2)
        self.assertLess(result['net_proceeds'], selling_price_with_vat)

    def test_calculate_total_fees_different_categories(self):
        """Test total fees calculation with different product categories"""
        price = 100.0
        
        # Test electronics (8% referral fee)
        result_electronics = self.fees_calc.calculate_total_fees(price, category='electronics')
        self.assertEqual(result_electronics['referral_fee'], 8.0)
        self.assertEqual(result_electronics['fee_breakdown']['referral_percentage'], 8.0)
        self.assertEqual(result_electronics['fee_breakdown']['category'], 'electronics')
        
        # Test clothing (17% referral fee)
        result_clothing = self.fees_calc.calculate_total_fees(price, category='clothing')
        self.assertEqual(result_clothing['referral_fee'], 17.0)
        self.assertEqual(result_clothing['fee_breakdown']['referral_percentage'], 17.0)

    def test_calculate_total_fees_different_weights(self):
        """Test total fees calculation with different weights"""
        price = 50.0
        
        # Light item (0.5kg)
        result_light = self.fees_calc.calculate_total_fees(price, weight_kg=0.5)
        self.assertEqual(result_light['fba_fee'], 2.80)
        
        # Medium item (2kg)
        result_medium = self.fees_calc.calculate_total_fees(price, weight_kg=2.0)
        expected_medium_fba = 3.90 + (1.0 * 0.65)  # large_standard base + extra
        self.assertEqual(result_medium['fba_fee'], expected_medium_fba)
        
        # Heavy item (12kg)
        result_heavy = self.fees_calc.calculate_total_fees(price, weight_kg=12.0)
        expected_heavy_fba = 6.90 + (11.0 * 0.85)  # small_oversize base + extra
        self.assertEqual(result_heavy['fba_fee'], expected_heavy_fba)

    def test_calculate_fees_simplified_method(self):
        """Test the simplified calculate_fees method"""
        selling_price = 29.99
        weight = 0.5
        category = 'electronics'
        
        simple_result = self.fees_calc.calculate_fees(selling_price, weight, category)
        detailed_result = self.fees_calc.calculate_total_fees(selling_price, weight, category)
        
        self.assertEqual(simple_result, detailed_result['total_fees'])

    def test_fee_breakdown_content(self):
        """Test that fee breakdown contains correct information"""
        result = self.fees_calc.calculate_total_fees(50.0, weight_kg=1.5, category='toys')
        breakdown = result['fee_breakdown']
        
        self.assertEqual(breakdown['referral_percentage'], 15.0)  # toys category
        self.assertEqual(breakdown['weight_kg'], 1.5)
        self.assertEqual(breakdown['category'], 'toys')

    def test_edge_cases_zero_price(self):
        """Test edge case with zero selling price"""
        result = self.fees_calc.calculate_total_fees(0.0)
        
        self.assertEqual(result['referral_fee'], 0.0)
        self.assertEqual(result['fba_fee'], 2.80)  # FBA fee still applies
        self.assertEqual(result['closing_fee'], 0.0)
        self.assertEqual(result['total_fees'], 2.80)
        self.assertEqual(result['net_proceeds'], -2.80)  # Negative because of FBA fee

    def test_edge_cases_very_high_price(self):
        """Test edge case with very high selling price"""
        high_price = 9999.99
        result = self.fees_calc.calculate_total_fees(high_price)
        
        expected_referral = high_price * 0.15
        self.assertAlmostEqual(result['referral_fee'], expected_referral, places=2)
        self.assertGreater(result['total_fees'], expected_referral)  # Includes FBA fee
        self.assertGreater(result['net_proceeds'], 0)  # Should still be profitable

    def test_precision_and_rounding(self):
        """Test that calculations maintain appropriate precision"""
        price = 19.99
        result = self.fees_calc.calculate_total_fees(price)
        
        # All monetary values should be reasonable precision
        self.assertIsInstance(result['referral_fee'], float)
        self.assertIsInstance(result['fba_fee'], float)
        self.assertIsInstance(result['total_fees'], float)
        self.assertIsInstance(result['net_proceeds'], float)
        
        # Total should equal sum of components
        calculated_total = result['referral_fee'] + result['fba_fee'] + result['closing_fee']
        self.assertAlmostEqual(result['total_fees'], calculated_total, places=10)


if __name__ == '__main__':
    # Run tests with detailed output
    unittest.main(verbosity=2)
