#!/usr/bin/env python3
"""
Comprehensive test suite for enhanced Amazon fees calculator
"""

import unittest
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.enhanced_amazon_fees import EnhancedAmazonFeesCalculator
from core.enhanced_roi_calculator import EnhancedROICalculator
from utils.config import Config

class TestEnhancedAmazonFees(unittest.TestCase):
    """Test enhanced Amazon fees calculator"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = Config()
        self.calculator = EnhancedAmazonFeesCalculator(config=self.config)
    
    def test_basic_fee_calculation(self):
        """Test basic fee calculation without dimensions"""
        result = self.calculator.calculate_comprehensive_fees(
            selling_price=12.89,
            weight_kg=0.11,
            category='beauty'
        )
        
        # Verify basic fee components
        self.assertIn('referral_fee', result)
        self.assertIn('fba_fee', result)
        self.assertIn('closing_fee', result)
        self.assertIn('storage_fee', result)
        self.assertIn('total_fees', result)
        
        # Check fee values are reasonable
        self.assertGreater(result['referral_fee'], 0)
        self.assertGreater(result['fba_fee'], 0)
        self.assertEqual(result['closing_fee'], 0)  # No closing fee for beauty
        self.assertEqual(result['storage_fee'], 0)  # No storage without dimensions
        
        # Total should equal sum of components
        expected_total = (result['referral_fee'] + result['fba_fee'] + 
                         result['closing_fee'] + result['storage_fee'] +
                         result['prep_fee'] + result['inbound_shipping'] +
                         result['digital_services'] + result['misc_fee'] +
                         result['vat_on_fees'])
        self.assertAlmostEqual(result['total_fees'], expected_total, places=4)
    
    def test_storage_fee_calculation(self):
        """Test storage fee calculation with dimensions"""
        # Simulate Keepa data with dimensions
        keepa_data = {
            'packageLength': 156,  # mm
            'packageWidth': 50,    # mm
            'packageHeight': 32,   # mm
            'packageWeight': 110   # grams
        }
        
        result = self.calculator.calculate_comprehensive_fees(
            selling_price=12.89,
            weight_kg=0.11,
            category='beauty',
            keepa_data=keepa_data
        )
        
        # Storage fee should be calculated
        self.assertGreater(result['storage_fee'], 0)
        
        # Check storage details
        storage_details = result['storage_details']
        self.assertTrue(storage_details['calculation_possible'])
        self.assertIn('volume_m3', storage_details)
        self.assertIn('size_category', storage_details)
        self.assertEqual(storage_details['storage_months'], 3)  # Default
    
    def test_size_classification(self):
        """Test Amazon size classification"""
        # Test standard size product
        standard_dimensions = (400, 300, 200)  # mm, within standard limits
        size_cat = self.calculator.classify_product_size(
            standard_dimensions, 1000  # 1kg
        )
        self.assertEqual(size_cat, 'standard_size')
        
        # Test oversize product (exceeds length limit)
        oversize_dimensions = (500, 300, 200)  # mm, exceeds 45cm length
        size_cat = self.calculator.classify_product_size(
            oversize_dimensions, 1000
        )
        self.assertEqual(size_cat, 'oversize')


class TestEnhancedROICalculator(unittest.TestCase):
    """Test enhanced ROI calculator"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = Config()
        self.calculator = EnhancedROICalculator(config=self.config)
    
    def test_comprehensive_roi_calculation(self):
        """Test comprehensive ROI calculation"""
        result = self.calculator.calculate_comprehensive_roi(
            cost_price=8.50,
            selling_price=12.89,
            weight_kg=0.11,
            category='beauty'
        )
        
        # Verify all required fields are present
        required_fields = [
            'original_cost_price', 'original_selling_price', 'profit',
            'roi_percentage', 'profit_margin', 'is_profitable',
            'total_amazon_fees', 'net_proceeds', 'profitability_score',
            'amazon_fees_breakdown', 'calculation_notes'
        ]
        
        for field in required_fields:
            self.assertIn(field, result, f"Missing field: {field}")
        
        # Check ROI calculation logic
        expected_profit = result['net_proceeds'] - result['cost_including_vat']
        self.assertAlmostEqual(result['profit'], expected_profit, places=2)
    
    def test_break_even_calculation(self):
        """Test break-even price calculation"""
        result = self.calculator.calculate_break_even_price(
            cost_price=8.50,
            weight_kg=0.11,
            category='beauty',
            target_roi=20.0
        )
        
        # Verify break-even structure
        self.assertIn('break_even_price', result)
        self.assertIn('target_roi', result)
        self.assertIn('achieved_roi', result)
        self.assertIn('detailed_calculation', result)
        
        # Break-even price should be higher than cost
        self.assertGreater(result['break_even_price'], 8.50)


if __name__ == '__main__':
    # Configure test runner
    unittest.main(verbosity=2, buffer=True)
