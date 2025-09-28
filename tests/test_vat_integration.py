"""
Integration tests for VAT functionality across the entire application
"""

import unittest
import tempfile
import os
from utils.config import Config
from core.amazon_fees import AmazonFeesCalculator
from core.roi_calculator import ROICalculator
from gui.main_window import AnalysisWorker

class TestVATIntegration(unittest.TestCase):
    """Integration tests for VAT functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_config_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        self.temp_config_file.close()
    
    def tearDown(self):
        """Clean up test fixtures"""
        try:
            if os.path.exists(self.temp_config_file.name):
                os.remove(self.temp_config_file.name)
        except OSError:
            pass
    
    def test_end_to_end_vat_workflow_no_vat_on_cost(self):
        """Test complete workflow with VAT disabled on cost"""
        # Step 1: Configure no VAT on cost
        config = Config()
        config.set_vat_rate(20.0)
        config.set_apply_vat_on_cost(False)
        config.set_apply_vat_on_sale(False)
        
        # Step 2: Initialize calculators
        fees_calc = AmazonFeesCalculator('france', config)
        roi_calc = ROICalculator(config)
        
        # Step 3: Same test scenario
        original_cost = 50.0
        selling_price = 120.0
        weight = 0.8
        
        # Step 4: Calculate
        fee_result = fees_calc.calculate_total_fees(selling_price, weight)
        roi_result = roi_calc.calculate_roi(original_cost, selling_price, fee_result['total_fees'])
        
        # Step 5: Verify VAT was NOT applied to cost
        self.assertAlmostEqual(roi_result['cost_price'], original_cost, places=2)
        
        # Step 6: Should have higher ROI than with VAT scenario
        self.assertGreater(roi_result['roi_percentage'], 0)
    
    def test_breakeven_analysis_with_vat(self):
        """Test breakeven analysis integration with VAT"""
        config = Config()
        config.set_vat_rate(20.0)
        config.set_apply_vat_on_cost(True)
        
        roi_calc = ROICalculator(config)
        
        # Test breakeven calculation
        cost_price = 30.0
        target_roi = 25.0
        amazon_fee_percentage = 15.0
        fba_fee = 3.50
        
        breakeven_price = roi_calc.calculate_breakeven_price(
            cost_price, amazon_fee_percentage, fba_fee, target_roi
        )
        
        # Verify breakeven price accounts for VAT on cost
        # With VAT, effective cost becomes 30 * 1.20 = 36.0
        # Should result in higher breakeven price than without VAT
        self.assertGreater(breakeven_price, 50.0)
        
        # Test the breakeven price actually achieves target ROI
        fees_calc = AmazonFeesCalculator('france', config)
        fee_result = fees_calc.calculate_total_fees(breakeven_price)
        roi_result = roi_calc.calculate_roi(cost_price, breakeven_price, fee_result['total_fees'])
        
        # Should be close to target ROI (within reasonable margin due to simplified fee calc)
        self.assertGreater(roi_result['roi_percentage'], target_roi - 5.0)
    
    def test_error_handling_integration(self):
        """Test error handling across VAT integration"""
        # Test with invalid VAT rates
        config = Config()
        
        with self.assertRaises(ValueError):
            config.set_vat_rate(-5.0)  # Negative VAT rate
        
        with self.assertRaises(ValueError):
            config.set_vat_rate(105.0)  # VAT rate over 100%
        
        # Test with valid edge cases
        config.set_vat_rate(0.0)  # Zero VAT should work
        fees_calc = AmazonFeesCalculator('france', config)
        roi_calc = ROICalculator(config)
        
        result = roi_calc.calculate_roi(50.0, 100.0, 15.0)
        self.assertEqual(result['cost_price'], 50.0)  # No VAT applied
    
    def test_backward_compatibility(self):
        """Test that existing functionality still works without explicit VAT configuration"""
        # Test with default configuration (minimal setup)
        fees_calc = AmazonFeesCalculator('france')
        roi_calc = ROICalculator()
        
        # Should still work with basic functionality
        fee_result = fees_calc.calculate_total_fees(100.0)
        roi_result = roi_calc.calculate_roi(30.0, 100.0, fee_result['total_fees'])
        
        # Should have reasonable results
        self.assertGreater(fee_result['total_fees'], 0)
        self.assertIsInstance(roi_result['roi_percentage'], float)
        
        # Should maintain backward compatibility
        self.assertIn('referral_fee', fee_result)
        self.assertIn('fba_fee', fee_result)
        self.assertIn('profit', roi_result)

if __name__ == '__main__':
    unittest.main()
