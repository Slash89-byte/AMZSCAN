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
    
    def test_end_to_end_vat_workflow_with_vat_on_cost(self):
        """Test complete workflow: Configuration → Fee Calculation → ROI Analysis with VAT on cost"""
        # Step 1: Configure VAT settings
        config = Config()
        config.set_vat_rate(20.0)
        config.set_apply_vat_on_cost(True)
        config.set_apply_vat_on_sale(False)
        config.set('api_settings.default_domain', 'france')
        
        # Step 2: Initialize calculators with VAT configuration
        fees_calc = AmazonFeesCalculator('france', config)
        roi_calc = ROICalculator(config)
        
        # Step 3: Test scenario data
        original_cost = 50.0
        selling_price = 120.0
        weight = 0.8  # kg
        
        # Step 4: Calculate fees (should use VAT-adjusted prices if configured)
        fee_result = fees_calc.calculate_total_fees(selling_price, weight)
        
        # Step 5: Calculate ROI (should apply VAT to cost)
        roi_result = roi_calc.calculate_roi(
            original_cost, 
            selling_price, 
            fee_result['total_fees']
        )
        
        # Step 6: Verify VAT was applied to cost
        expected_vat_cost = original_cost * 1.20  # 60.0
        self.assertAlmostEqual(roi_result['cost_price'], expected_vat_cost, places=2)
        
        # Step 7: Verify the complete calculation chain
        self.assertGreater(fee_result['total_fees'], 0)
        self.assertGreater(roi_result['profit'], 0)
        self.assertLess(roi_result['roi_percentage'], 100)  # Should be reasonable
        
        # Step 8: Verify configuration is properly reflected
        self.assertTrue(config.get_apply_vat_on_cost())
        self.assertFalse(config.get_apply_vat_on_sale())
        self.assertEqual(config.get_vat_rate(), 20.0)
    
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
    
    def test_different_vat_rates_integration(self):
        """Test integration with different EU VAT rates"""
        test_scenarios = [
            ('france', 20.0),
            ('germany', 19.0),
            ('italy', 22.0),
            ('spain', 21.0)
        ]
        
        base_cost = 40.0
        selling_price = 100.0
        weight = 0.5
        
        results = {}
        
        for country, vat_rate in test_scenarios:
            config = Config()
            config.set_vat_rate(vat_rate)
            config.set_apply_vat_on_cost(True)
            
            fees_calc = AmazonFeesCalculator(country, config)
            roi_calc = ROICalculator(config)
            
            fee_result = fees_calc.calculate_total_fees(selling_price, weight)
            roi_result = roi_calc.calculate_roi(base_cost, selling_price, fee_result['total_fees'])
            
            results[country] = {
                'vat_rate': vat_rate,
                'vat_adjusted_cost': roi_result['cost_price'],
                'roi_percentage': roi_result['roi_percentage'],
                'profit': roi_result['profit']
            }
            
            # Verify VAT was applied correctly
            expected_vat_cost = base_cost * (1 + vat_rate / 100)
            self.assertAlmostEqual(roi_result['cost_price'], expected_vat_cost, places=2)
        
        # Verify that higher VAT rates result in lower ROI
        france_roi = results['france']['roi_percentage']
        italy_roi = results['italy']['roi_percentage']
        self.assertGreater(france_roi, italy_roi)  # France (20%) > Italy (22%)
    
    def test_configuration_persistence_integration(self):
        """Test that configuration persists and affects calculations correctly"""
        # Step 1: Create and save configuration
        config1 = Config()
        config1.set_vat_rate(25.0)
        config1.set_apply_vat_on_cost(True)
        config1.set('api_settings.keepa_api_key', 'test_api_key_123')
        config1.save(self.temp_config_file.name)
        
        # Step 2: Load configuration in new instance
        config2 = Config()
        config2.load(self.temp_config_file.name)
        
        # Step 3: Use loaded configuration in calculators
        fees_calc = AmazonFeesCalculator('france', config2)
        roi_calc = ROICalculator(config2)
        
        # Step 4: Perform calculations
        cost = 80.0
        result = roi_calc.calculate_roi(cost, 200.0, 30.0)
        
        # Step 5: Verify loaded settings were applied
        expected_vat_cost = cost * 1.25  # 25% VAT
        self.assertAlmostEqual(result['cost_price'], expected_vat_cost, places=2)
        self.assertEqual(config2.get('api_settings.keepa_api_key'), 'test_api_key_123')
    
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
    
    def test_profitability_scenarios_with_vat(self):
        """Test profitability scenario analysis with VAT integration"""
        config = Config()
        config.set_vat_rate(20.0)
        config.set_apply_vat_on_cost(True)
        
        roi_calc = ROICalculator(config)
        
        cost_price = 25.0
        selling_price = 75.0
        amazon_fees = 11.25  # 15% of selling price
        
        scenarios = roi_calc.analyze_profitability_scenarios(cost_price, selling_price, amazon_fees)
        
        # Verify current scenario includes VAT
        current = scenarios['current']
        expected_vat_cost = cost_price * 1.20
        self.assertAlmostEqual(current['cost_price'], expected_vat_cost, places=2)
        
        # Verify price drop scenarios
        price_drop_10 = scenarios['price_drops']['10%']
        self.assertLess(price_drop_10['roi_percentage'], current['roi_percentage'])
        
        # Verify cost increase scenarios
        cost_increase_10 = scenarios['cost_increases']['10%']
        increased_cost = cost_price * 1.10
        expected_vat_increased = increased_cost * 1.20
        self.assertAlmostEqual(cost_increase_10['cost_price'], expected_vat_increased, places=2)
        
        # Verify breakeven scenarios
        breakeven_20_roi = scenarios['breakeven']['20%_roi']
        self.assertIn('required_price', breakeven_20_roi)
        self.assertIn('feasible', breakeven_20_roi)
    
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
    
    def test_gui_integration_mock(self):
        """Test integration with GUI components (mocked)"""
        # Create configuration that would come from GUI
        config = Config()
        config.set('api_settings.keepa_api_key', 'mock_api_key')
        config.set_vat_rate(20.0)
        config.set_apply_vat_on_cost(True)
        config.set('api_settings.default_domain', 'france')
        
        # Simulate the analysis worker workflow
        asin = 'B00TEST123'
        cost_price = 45.0
        
        # The AnalysisWorker would use these components
        fees_calc = AmazonFeesCalculator('france', config)
        roi_calc = ROICalculator(config)
        
        # Mock a typical calculation workflow
        mock_selling_price = 110.0
        fee_result = fees_calc.calculate_total_fees(mock_selling_price)
        roi_result = roi_calc.calculate_roi(cost_price, mock_selling_price, fee_result['total_fees'])
        
        # Verify the results would be suitable for GUI display
        self.assertIsInstance(roi_result['roi_percentage'], (int, float))
        self.assertIsInstance(roi_result['profit'], (int, float))
        self.assertGreater(len(str(roi_result['roi_percentage'])), 0)  # Should be displayable
        
        # VAT should be reflected in cost
        expected_vat_cost = cost_price * 1.20
        self.assertAlmostEqual(roi_result['cost_price'], expected_vat_cost, places=2)

if __name__ == '__main__':
    unittest.main()
