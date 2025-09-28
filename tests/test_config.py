"""
Unit tests for the Configuration system
"""

import unittest
import tempfile
import json
import os
from unittest.mock import patch
from utils.config import Config

class TestConfig(unittest.TestCase):
    """Test cases for the Config class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.temp_dir, 'test_config.json')
        
    def tearDown(self):
        """Clean up test fixtures"""
        try:
            if os.path.exists(self.config_file):
                os.remove(self.config_file)
            # Only remove directory if it's empty
            if os.path.exists(self.temp_dir) and not os.listdir(self.temp_dir):
                os.rmdir(self.temp_dir)
        except (OSError, IOError):
            # Ignore cleanup errors
            pass
    
    def test_default_configuration(self):
        """Test that default configuration is properly loaded"""
        config = Config()
        
        # Test API settings
        api_settings = config.get('api_settings', {})
        self.assertEqual(api_settings.get('keepa_api_key'), '')
        self.assertEqual(api_settings.get('default_domain'), 'france')
        
        # Test VAT settings
        vat_settings = config.get('vat_settings', {})
        self.assertEqual(vat_settings.get('vat_rate'), 20.0)
        self.assertTrue(vat_settings.get('apply_vat_on_cost'))
        self.assertFalse(vat_settings.get('apply_vat_on_sales'))
        
        # Test analysis settings
        analysis_settings = config.get('analysis_settings', {})
        self.assertEqual(analysis_settings.get('min_roi_threshold'), 15.0)
        self.assertEqual(analysis_settings.get('max_cost_price'), 500.0)
        
        # Test business model settings
        business_settings = config.get('business_model_settings', {})
        self.assertEqual(business_settings.get('business_model'), 'retail_arbitrage')
        self.assertEqual(business_settings.get('risk_tolerance'), 'medium')
    
    def test_get_method(self):
        """Test the get method with different scenarios"""
        config = Config()
        
        # Test getting existing key
        self.assertEqual(config.get('api_settings.keepa_api_key'), '')
        
        # Test getting non-existing key with default
        self.assertEqual(config.get('non_existent_key', 'default'), 'default')
        
        # Test getting nested key
        vat_rate = config.get('vat_settings.vat_rate')
        self.assertEqual(vat_rate, 20.0)
    
    def test_set_method(self):
        """Test the set method"""
        config = Config()
        
        # Test setting simple key
        config.set('api_settings.keepa_api_key', 'test_api_key')
        self.assertEqual(config.get('api_settings.keepa_api_key'), 'test_api_key')
        
        # Test setting new nested key
        config.set('new_section.new_key', 'new_value')
        self.assertEqual(config.get('new_section.new_key'), 'new_value')
    
    def test_vat_helper_methods(self):
        """Test VAT-specific helper methods"""
        config = Config()
        
        # Test default VAT rate
        self.assertEqual(config.get_vat_rate(), 20.0)
        
        # Test setting VAT rate
        config.set_vat_rate(21.0)
        self.assertEqual(config.get_vat_rate(), 21.0)
        
        # Test default VAT application on cost
        self.assertTrue(config.get_apply_vat_on_cost())
        
        # Test setting VAT application on cost
        config.set_apply_vat_on_cost(False)
        self.assertFalse(config.get_apply_vat_on_cost())
        
        # Test default VAT application on sales
        self.assertFalse(config.get_apply_vat_on_sale())
        
        # Test setting VAT application on sales
        config.set_apply_vat_on_sale(True)
        self.assertTrue(config.get_apply_vat_on_sale())
    
    def test_save_and_load_configuration(self):
        """Test saving and loading configuration"""
        # Create config with custom settings
        config1 = Config()
        config1.set('api_settings.keepa_api_key', 'test_key_123')
        config1.set_vat_rate(19.0)
        config1.set_apply_vat_on_cost(False)
        
        # Save configuration
        config1.save(self.config_file)
        self.assertTrue(os.path.exists(self.config_file))
        
        # Load configuration in new instance
        config2 = Config()
        config2.load(self.config_file)
        
        # Verify settings were preserved
        self.assertEqual(config2.get('api_settings.keepa_api_key'), 'test_key_123')
        self.assertEqual(config2.get_vat_rate(), 19.0)
        self.assertFalse(config2.get_apply_vat_on_cost())
    
    def test_validation_methods(self):
        """Test configuration validation"""
        config = Config()
        
        # Test VAT rate validation
        self.assertTrue(config.validate_vat_rate(20.0))
        self.assertTrue(config.validate_vat_rate(0.0))
        self.assertFalse(config.validate_vat_rate(-1.0))
        self.assertFalse(config.validate_vat_rate(101.0))
        
        # Test ROI threshold validation
        self.assertTrue(config.validate_roi_threshold(15.0))
        self.assertTrue(config.validate_roi_threshold(0.0))
        self.assertFalse(config.validate_roi_threshold(-1.0))
        self.assertFalse(config.validate_roi_threshold(1000.1))
        
        # Test cost price validation
        self.assertTrue(config.validate_max_cost_price(500.0))
        self.assertTrue(config.validate_max_cost_price(1.0))
        self.assertFalse(config.validate_max_cost_price(0.0))
        self.assertFalse(config.validate_max_cost_price(10001.0))
    
    def test_domain_configuration(self):
        """Test domain-specific configuration"""
        config = Config()
        
        # Test default domain
        self.assertEqual(config.get('api_settings.default_domain'), 'france')
        
        # Test setting domain
        config.set('api_settings.default_domain', 'germany')
        self.assertEqual(config.get('api_settings.default_domain'), 'germany')
        
        # Test domain-specific VAT rates (if implemented)
        config.set('api_settings.default_domain', 'germany')
        config.set_vat_rate(19.0)  # Germany VAT rate
        self.assertEqual(config.get_vat_rate(), 19.0)
    
    def test_business_model_configuration(self):
        """Test business model settings"""
        config = Config()
        
        # Test default business model
        self.assertEqual(config.get('business_model_settings.business_model'), 'retail_arbitrage')
        
        # Test setting business model
        config.set('business_model_settings.business_model', 'private_label')
        self.assertEqual(config.get('business_model_settings.business_model'), 'private_label')
        
        # Test risk tolerance
        self.assertEqual(config.get('business_model_settings.risk_tolerance'), 'medium')
        config.set('business_model_settings.risk_tolerance', 'high')
        self.assertEqual(config.get('business_model_settings.risk_tolerance'), 'high')
    
    def test_analysis_settings(self):
        """Test analysis configuration"""
        config = Config()
        
        # Test default analysis settings
        analysis_settings = config.get('analysis_settings', {})
        self.assertEqual(analysis_settings.get('min_roi_threshold'), 15.0)
        self.assertEqual(analysis_settings.get('max_cost_price'), 500.0)
        self.assertEqual(analysis_settings.get('max_acceptable_sales_rank'), 100000)
        
        # Test updating analysis settings
        config.set('analysis_settings.min_roi_threshold', 20.0)
        config.set('analysis_settings.max_cost_price', 750.0)
        
        self.assertEqual(config.get('analysis_settings.min_roi_threshold'), 20.0)
        self.assertEqual(config.get('analysis_settings.max_cost_price'), 750.0)
    
    def test_error_handling(self):
        """Test error handling in configuration"""
        config = Config()
        
        # Test loading non-existent file
        non_existent_file = os.path.join(self.temp_dir, 'non_existent.json')
        config.load(non_existent_file)  # Should not raise exception
        
        # Test loading invalid JSON
        invalid_json_file = os.path.join(self.temp_dir, 'invalid.json')
        with open(invalid_json_file, 'w') as f:
            f.write('invalid json content')
        
        config.load(invalid_json_file)  # Should not raise exception
        
        # Test setting invalid VAT rate
        with self.assertRaises(ValueError):
            config.set_vat_rate(-5.0)
        
        with self.assertRaises(ValueError):
            config.set_vat_rate(105.0)
    
    def test_configuration_dialog_integration(self):
        """Test integration with configuration dialog"""
        config = Config()
        
        # Test that configuration can be properly serialized for GUI
        config_dict = config.get_all()
        self.assertIsInstance(config_dict, dict)
        
        # Test all required sections exist
        required_sections = [
            'api_settings', 'vat_settings', 'analysis_settings',
            'business_model_settings', 'advanced_settings'
        ]
        
        for section in required_sections:
            self.assertIn(section, config_dict)
    
    def test_migration_and_backward_compatibility(self):
        """Test configuration migration for backward compatibility"""
        # Create old-style configuration
        old_config = {
            'keepa_api_key': 'old_api_key',
            'vat_rate': 21.0
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(old_config, f)
        
        # Load in new configuration system
        config = Config()
        config.load(self.config_file)
        
        # Test that old configuration is accessible through both old and new paths
        self.assertEqual(config.get('keepa_api_key', ''), 'old_api_key')
        # Note: In real implementation, you might have migration logic here

if __name__ == '__main__':
    unittest.main()
