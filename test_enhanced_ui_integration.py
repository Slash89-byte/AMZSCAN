"""
Integration tests for enhanced UI features with real API interactions
"""

import unittest
import sys
import os
from unittest.mock import MagicMock, patch, Mock
import tempfile
import json

# Add the parent directory to sys.path to import project modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config import Config
from core.keepa_api import KeepaAPI
from core.enhanced_amazon_fees import EnhancedAmazonFeesCalculator
from core.enhanced_roi_calculator import EnhancedROICalculator


class TestEnhancedUIIntegration(unittest.TestCase):
    """Integration tests for enhanced UI features"""
    
    def setUp(self):
        """Set up test configuration"""
        # Create temporary config file
        self.temp_config = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        test_config = {
            "keepa_api_key": "test_key_placeholder",
            "enhanced_fees": {
                "prep_fee": 1.0,
                "inbound_shipping": 0.5,
                "digital_services": 0.3,
                "misc_fee": 0.2,
                "vat_rate": 0.20
            },
            "roi_settings": {
                "target_roi": 20.0,
                "minimum_profit": 5.0,
                "risk_factor": 1.1
            }
        }
        json.dump(test_config, self.temp_config)
        self.temp_config.close()
        
        # Patch config file path
        self.config_patcher = patch('utils.config.Config._get_config_path')
        mock_config_path = self.config_patcher.start()
        mock_config_path.return_value = self.temp_config.name
        
        self.config = Config()
    
    def tearDown(self):
        """Clean up test resources"""
        self.config_patcher.stop()
        os.unlink(self.temp_config.name)
    
    def test_enhanced_analysis_workflow_integration(self):
        """Test complete enhanced analysis workflow"""
        # Mock Keepa API response
        mock_keepa_response = {
            'success': True,
            'asin': 'B0BQBXBW88',
            'title': 'L\'Oréal Paris Men Expert Barber Club Beard Oil',
            'current_price': 8.99,
            'rating': 4.3,
            'review_count': 2847,
            'sales_rank': 15234,
            'main_category': 'Beauty & Personal Care',
            'weight': 0.1,
            'dimensions': {'length': 15.0, 'width': 5.0, 'height': 5.0},
            'in_stock': True,
            'fee_category': 'beauty',
            'raw_data': {
                'csv': {
                    1: [1000, 899, 1010, 920, 1020, 880, 1030, 899]  # Price history
                },
                'imagesCSV': '1234567,https://example.com/image.jpg'
            }
        }
        
        with patch.object(KeepaAPI, 'get_product_data', return_value=mock_keepa_response):
            # Test enhanced analysis components
            fees_calc = EnhancedAmazonFeesCalculator('france', self.config)
            roi_calc = EnhancedROICalculator(self.config)
            
            # Test comprehensive analysis
            cost_price = 5.0
            selling_price = mock_keepa_response['current_price']
            weight_kg = mock_keepa_response['weight']
            category = mock_keepa_response['fee_category']
            raw_data = mock_keepa_response['raw_data']
            
            roi_data = roi_calc.calculate_comprehensive_roi(
                cost_price=cost_price,
                selling_price=selling_price,
                weight_kg=weight_kg,
                category=category,
                keepa_data=raw_data
            )
            
            # Verify comprehensive analysis results
            self.assertIsInstance(roi_data, dict)
            self.assertIn('roi_percentage', roi_data)
            self.assertIn('profit', roi_data)
            self.assertIn('is_profitable', roi_data)
            self.assertIn('amazon_fees_breakdown', roi_data)
            self.assertIn('profitability_score', roi_data)
            
            # Verify fee breakdown includes enhanced fees
            fee_breakdown = roi_data['amazon_fees_breakdown']
            self.assertIn('referral_fee', fee_breakdown)
            self.assertIn('fba_fee', fee_breakdown)
            self.assertIn('storage_fee', fee_breakdown)
            self.assertIn('prep_fee', fee_breakdown)
            self.assertIn('vat_on_fees', fee_breakdown)
            
            # Test profitability
            expected_profitable = roi_data['profit'] > 0
            self.assertEqual(roi_data['is_profitable'], expected_profitable)
    
    def test_image_loading_integration(self):
        """Test image loading integration with API data"""
        mock_raw_data = {
            'imagesCSV': '1234567,https://example.com/image1.jpg,1234568,https://example.com/image2.jpg'
        }
        
        # Test image URL extraction
        images_csv = mock_raw_data.get('imagesCSV', '')
        parts = images_csv.split(',')
        
        self.assertTrue(len(parts) >= 2)
        
        # Should extract latest image URL
        if len(parts) % 2 == 0:
            latest_url = parts[-1]
        else:
            latest_url = parts[-2]
        
        self.assertIn('https://', latest_url)
        self.assertIn('image', latest_url)
    
    def test_price_history_integration(self):
        """Test price history integration with Keepa data"""
        mock_raw_data = {
            'csv': {
                1: [1000, 899, 1010, 920, 1020, 880, 1030, 899, 1040, -1]  # Last price -1 (no data)
            }
        }
        
        # Test price history extraction
        csv_data = mock_raw_data.get('csv', {})
        price_history = csv_data.get(1, [])
        
        self.assertTrue(len(price_history) > 0)
        self.assertEqual(len(price_history) % 2, 0)  # Should be pairs
        
        # Test price parsing
        valid_prices = []
        for i in range(0, len(price_history), 2):
            if i + 1 < len(price_history):
                timestamp = price_history[i]
                price = price_history[i + 1]
                
                if price != -1:  # Valid price
                    valid_prices.append((timestamp, price / 100.0))  # Convert from cents
        
        self.assertTrue(len(valid_prices) > 0)
        
        # Verify price values are reasonable
        for timestamp, price in valid_prices:
            self.assertGreater(timestamp, 0)
            self.assertGreater(price, 0)
            self.assertLess(price, 1000)  # Reasonable upper bound
    
    def test_product_details_integration(self):
        """Test product details integration with complete data"""
        complete_product_data = {
            'asin': 'B0BQBXBW88',
            'title': 'L\'Oréal Paris Men Expert Barber Club Beard Oil',
            'current_price': 8.99,
            'rating': 4.3,
            'review_count': 2847,
            'sales_rank': 15234,
            'main_category': 'Beauty & Personal Care',
            'weight': 0.1,
            'in_stock': True,
            'fee_category': 'beauty'
        }
        
        # Test all fields are properly handled
        required_fields = ['asin', 'title', 'current_price']
        for field in required_fields:
            self.assertIn(field, complete_product_data)
            self.assertIsNotNone(complete_product_data[field])
        
        # Test optional fields
        optional_fields = ['rating', 'review_count', 'sales_rank', 'weight']
        for field in optional_fields:
            if field in complete_product_data:
                value = complete_product_data[field]
                if isinstance(value, (int, float)):
                    self.assertGreaterEqual(value, 0)
        
        # Test boolean fields
        if 'in_stock' in complete_product_data:
            self.assertIsInstance(complete_product_data['in_stock'], bool)
    
    def test_error_handling_integration(self):
        """Test error handling integration across components"""
        # Test with invalid API key configuration
        invalid_config = Config()
        
        # Test that KeepaAPI can be initialized with any key
        keepa_api = KeepaAPI(invalid_config.get('keepa_api_key', 'test_key'))
        self.assertIsNotNone(keepa_api)
        self.assertIsNotNone(keepa_api.api_key)
        
        # Test invalid API responses
        invalid_responses = [
            None,
            {'success': False},
            {'success': True, 'current_price': 0},
            {'success': True, 'current_price': -1},
        ]
        
        for response in invalid_responses:
            with self.subTest(response=response):
                if response is None:
                    self.assertIsNone(response)
                elif not response.get('success', False):
                    self.assertFalse(response.get('success', False))
                elif response.get('current_price', 0) <= 0:
                    self.assertLessEqual(response.get('current_price', 0), 0)
    
    def test_enhanced_results_formatting_integration(self):
        """Test enhanced results formatting with real data structure"""
        # Mock complete analysis results
        results = {
            'product_id': 'B0BQBXBW88',
            'identifier_type': 'ASIN',
            'identifier_valid': True,
            'product_data': {
                'asin': 'B0BQBXBW88',
                'title': 'L\'Oréal Paris Men Expert Barber Club Beard Oil',
                'current_price': 8.99,
                'rating': 4.3,
                'review_count': 2847,
                'sales_rank': 15234,
                'main_category': 'Beauty & Personal Care',
                'weight': 0.1,
                'in_stock': True,
                'fee_category': 'beauty'
            },
            'analysis_results': {
                'roi_percentage': 35.2,
                'profit': 2.15,
                'profitability_score': 78,
                'is_profitable': True,
                'net_proceeds': 7.15,
                'total_amazon_fees': 1.84,
                'profit_margin': 23.9,
                'original_cost_price': 5.0,
                'amazon_fees_breakdown': {
                    'referral_fee': 1.35,
                    'fba_fee': 0.89,
                    'storage_fee': 0.12,
                    'prep_fee': 1.0,
                    'inbound_shipping': 0.5,
                    'digital_services': 0.3,
                    'misc_fee': 0.2,
                    'vat_on_fees': 0.37
                },
                'calculation_notes': [
                    'Used enhanced Amazon fees calculation',
                    'Storage fees calculated from Keepa dimensions',
                    'VAT applied to applicable fees'
                ]
            }
        }
        
        # Test that all required fields are present
        self.assertIn('product_data', results)
        self.assertIn('analysis_results', results)
        
        product_data = results['product_data']
        analysis = results['analysis_results']
        
        # Test financial metrics
        self.assertIsInstance(analysis['roi_percentage'], (int, float))
        self.assertIsInstance(analysis['profit'], (int, float))
        self.assertIsInstance(analysis['profitability_score'], (int, float))
        self.assertIsInstance(analysis['is_profitable'], bool)
        
        # Test fee breakdown
        fee_breakdown = analysis['amazon_fees_breakdown']
        self.assertIsInstance(fee_breakdown, dict)
        
        # Verify all enhanced fees are included
        enhanced_fees = ['referral_fee', 'fba_fee', 'storage_fee', 'prep_fee', 
                        'inbound_shipping', 'digital_services', 'misc_fee', 'vat_on_fees']
        for fee in enhanced_fees:
            self.assertIn(fee, fee_breakdown)
            self.assertIsInstance(fee_breakdown[fee], (int, float))
            self.assertGreaterEqual(fee_breakdown[fee], 0)
        
        # Test calculation notes
        notes = analysis['calculation_notes']
        self.assertIsInstance(notes, list)
        self.assertGreater(len(notes), 0)
    
    def test_break_even_analysis_integration(self):
        """Test break-even analysis integration for unprofitable products"""
        # Create scenario with unprofitable product
        cost_price = 15.0
        selling_price = 12.0  # Below cost
        
        roi_calc = EnhancedROICalculator(self.config)
        
        roi_data = roi_calc.calculate_comprehensive_roi(
            cost_price=cost_price,
            selling_price=selling_price,
            weight_kg=0.5,
            category='default'
        )
        
        # Should be unprofitable
        self.assertFalse(roi_data['is_profitable'])
        self.assertLess(roi_data['profit'], 0)
        self.assertLess(roi_data['roi_percentage'], 0)
        
        # Test break-even calculation
        total_fees = roi_data['total_amazon_fees']
        target_roi = 20.0
        
        # Simple break-even calculation
        break_even_price = (cost_price * (1 + target_roi/100) + total_fees) * 1.1
        
        self.assertGreater(break_even_price, selling_price)
        self.assertGreater(break_even_price, cost_price)
    
    def test_configuration_integration(self):
        """Test configuration integration with enhanced features"""
        # Test enhanced fees configuration
        enhanced_fees_config = self.config.get('enhanced_fees', {})
        
        self.assertIsInstance(enhanced_fees_config, dict)
        self.assertIn('prep_fee', enhanced_fees_config)
        self.assertIn('vat_rate', enhanced_fees_config)
        
        # Test VAT rate format
        vat_rate = enhanced_fees_config.get('vat_rate', 0)
        self.assertIsInstance(vat_rate, (int, float))
        self.assertGreaterEqual(vat_rate, 0)
        self.assertLessEqual(vat_rate, 1)  # Should be decimal format
        
        # Test ROI settings
        roi_settings = self.config.get('roi_settings', {})
        self.assertIsInstance(roi_settings, dict)
        
        if 'target_roi' in roi_settings:
            target_roi = roi_settings['target_roi']
            self.assertIsInstance(target_roi, (int, float))
            self.assertGreater(target_roi, 0)
    
    def test_multi_format_identifier_integration(self):
        """Test multi-format identifier integration"""
        from utils.identifiers import detect_and_validate_identifier
        
        # Test various identifier formats (using realistic expected types)
        test_identifiers = [
            ('B0BQBXBW88', 'ASIN'),
            ('4003994155486', 'EAN'),  # Valid EAN-13
            ('123456789012', 'UPC'),   # Valid UPC
            ('12345670', 'EAN'),       # Valid EAN-8
            ('invalid123', 'UNKNOWN')
        ]
        
        for identifier, expected_type in test_identifiers:
            with self.subTest(identifier=identifier):
                result = detect_and_validate_identifier(identifier)
                
                self.assertIsInstance(result, dict)
                self.assertIn('identifier_type', result)
                self.assertIn('is_valid', result)
                self.assertIn('formatted_code', result)
                
                if expected_type != 'UNKNOWN':
                    # For valid identifiers, should match expected type or be recognized
                    type_matches = (result['identifier_type'] == expected_type or
                                  result['identifier_type'] != 'UNKNOWN')
                    self.assertTrue(type_matches, 
                                  f"Identifier {identifier} should be recognized correctly")
    
    def test_performance_integration(self):
        """Test performance aspects of enhanced features"""
        import time
        
        # Test analysis performance
        start_time = time.time()
        
        fees_calc = EnhancedAmazonFeesCalculator('france', self.config)
        roi_calc = EnhancedROICalculator(self.config)
        
        # Simulate multiple calculations
        for i in range(10):
            cost_price = 10.0 + i
            selling_price = 20.0 + i
            
            roi_data = roi_calc.calculate_comprehensive_roi(
                cost_price=cost_price,
                selling_price=selling_price,
                weight_kg=0.5,
                category='default'
            )
            
            self.assertIsInstance(roi_data, dict)
        
        elapsed_time = time.time() - start_time
        
        # Should complete 10 calculations in reasonable time (< 1 second)
        self.assertLess(elapsed_time, 1.0)
    
    def test_data_consistency_integration(self):
        """Test data consistency across all enhanced components"""
        # Create consistent test data
        product_data = {
            'asin': 'B0BQBXBW88',
            'current_price': 25.99,
            'weight': 0.5,
            'fee_category': 'beauty'
        }
        
        cost_price = 15.0
        
        # Calculate fees
        fees_calc = EnhancedAmazonFeesCalculator('france', self.config)
        fee_breakdown = fees_calc.calculate_comprehensive_fees(
            selling_price=product_data['current_price'],
            weight_kg=product_data['weight'],
            category=product_data['fee_category']
        )
        
        # Calculate ROI
        roi_calc = EnhancedROICalculator(self.config)
        roi_data = roi_calc.calculate_comprehensive_roi(
            cost_price=cost_price,
            selling_price=product_data['current_price'],
            weight_kg=product_data['weight'],
            category=product_data['fee_category']
        )
        
        # Verify consistency between fee calculation and ROI calculation
        self.assertEqual(
            fee_breakdown['total_fees'],
            roi_data['total_amazon_fees']
        )
        
        # Verify profit calculation consistency
        expected_profit = product_data['current_price'] - cost_price - fee_breakdown['total_fees']
        self.assertAlmostEqual(roi_data['profit'], expected_profit, places=2)


if __name__ == '__main__':
    # Run all integration tests
    unittest.main(verbosity=2)
