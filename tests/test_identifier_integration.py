"""
Integration tests for multi-format identifier support
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.identifiers import ProductIdentifier, detect_and_validate_identifier
from core.keepa_api import KeepaAPI
from gui.main_window import AnalysisWorker
from utils.config import Config


class TestMultiFormatIdentifierIntegration(unittest.TestCase):
    """Integration tests for multi-format identifier support"""

    def setUp(self):
        """Set up test fixtures"""
        self.config = Config()
        self.config.set('keepa_api_key', 'test_key')

    def test_identifier_detection_integration(self):
        """Test complete identifier detection and validation"""
        test_cases = [
            # (input, expected_type, should_be_valid)
            ("B0BQBXBW88", "ASIN", True),
            ("4003994155486", "EAN", True),
            ("036000291452", "UPC", True),
            ("12345670", "EAN", True),  # EAN-8
            ("invalid_code", "UNKNOWN", False),
        ]

        for code, expected_type, expected_valid in test_cases:
            with self.subTest(code=code):
                result = detect_and_validate_identifier(code)
                
                self.assertEqual(result['identifier_type'], expected_type)
                self.assertEqual(result['is_valid'], expected_valid)
                self.assertEqual(result['can_use_for_lookup'], 
                               expected_valid and expected_type in ["ASIN", "EAN", "UPC", "GTIN"])

    @patch('core.keepa_api.requests.Session.get')
    def test_keepa_api_multi_format_support(self, mock_get):
        """Test KeepaAPI with different identifier types"""
        # Mock successful API response
        mock_response = Mock()
        mock_response.json.return_value = {
            'products': [{
                'asin': 'B0BQBXBW88',
                'title': 'Test Product',
                'csv': [[], [1289, 1299]],  # Buy Box empty, Amazon price has data
                'categoryTree': [{'name': 'Electronics'}]
            }]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        keepa_api = KeepaAPI('test_key')

        # Test ASIN lookup
        result_asin = keepa_api.get_product_data('B0BQBXBW88')
        self.assertIsNotNone(result_asin)
        # The result should contain success flag and data
        self.assertIn('success', result_asin)
        if result_asin.get('success') and result_asin.get('data'):
            self.assertIn('asin', result_asin['data'])

        # Test EAN lookup
        result_ean = keepa_api.get_product_data('4003994155486')
        self.assertIsNotNone(result_ean)

        # Verify API was called with correct parameters
        calls = mock_get.call_args_list
        
        # First call should use 'asin' parameter
        asin_call_params = calls[0][1]['params']
        self.assertIn('asin', asin_call_params)
        self.assertEqual(asin_call_params['asin'], 'B0BQBXBW88')

        # Second call should use 'code' parameter
        ean_call_params = calls[1][1]['params']
        self.assertIn('code', ean_call_params)
        self.assertEqual(ean_call_params['code'], '4003994155486')

    def test_keepa_api_invalid_identifier(self):
        """Test KeepaAPI with invalid identifier"""
        keepa_api = KeepaAPI('test_key')
        
        # Test with invalid identifier
        result = keepa_api.get_product_data('invalid_code')
        self.assertIsNone(result)

    @patch('core.keepa_api.KeepaAPI.get_product_data')
    def test_analysis_worker_multi_format(self, mock_get_product_data):
        """Test AnalysisWorker with different identifier types"""
        # Mock successful product data response
        mock_get_product_data.return_value = {
            'asin': 'B0BQBXBW88',
            'title': 'Test Product',
            'current_price': 12.89,
            'category': 'Electronics',
            'weight': 0.5,
            'fee_category': 'electronics'
        }

        # Test with ASIN
        worker_asin = AnalysisWorker('B0BQBXBW88', 10.0, self.config)
        
        # Mock the signals
        worker_asin.analysis_complete = Mock()
        worker_asin.error_occurred = Mock()

        # Run the worker
        worker_asin.run()

        # Verify analysis completed successfully
        self.assertTrue(worker_asin.analysis_complete.emit.called)
        self.assertFalse(worker_asin.error_occurred.emit.called)

        # Check the results
        call_args = worker_asin.analysis_complete.emit.call_args[0][0]
        self.assertEqual(call_args['identifier_type'], 'ASIN')
        self.assertEqual(call_args['product_id'], 'B0BQBXBW88')

        # Test with EAN
        worker_ean = AnalysisWorker('4003994155486', 10.0, self.config)
        worker_ean.analysis_complete = Mock()
        worker_ean.error_occurred = Mock()

        worker_ean.run()

        # Verify EAN analysis
        self.assertTrue(worker_ean.analysis_complete.emit.called)
        call_args_ean = worker_ean.analysis_complete.emit.call_args[0][0]
        self.assertEqual(call_args_ean['identifier_type'], 'EAN')
        self.assertEqual(call_args_ean['product_id'], '4003994155486')

    def test_identifier_normalization(self):
        """Test identifier normalization across formats"""
        test_cases = [
            # (input, expected_normalized)
            ("b0bqbxbw88", "B0BQBXBW88"),  # ASIN case conversion
            ("400-399-415-5486", "4003994155486"),  # EAN with separators
            ("036 000 291452", "036000291452"),  # UPC with spaces
            ("123-45670", "12345670"),  # EAN-8 with separator
        ]

        for input_code, expected_normalized in test_cases:
            with self.subTest(input_code=input_code):
                result = detect_and_validate_identifier(input_code)
                self.assertEqual(result['normalized_code'], expected_normalized)

    def test_error_handling_integration(self):
        """Test error handling across the identifier system"""
        # Test empty input
        result_empty = detect_and_validate_identifier("")
        self.assertEqual(result_empty['identifier_type'], "UNKNOWN")
        self.assertFalse(result_empty['is_valid'])

        # Test invalid format
        result_invalid = detect_and_validate_identifier("invalid123")
        self.assertEqual(result_invalid['identifier_type'], "UNKNOWN")
        self.assertFalse(result_invalid['is_valid'])

        # Test KeepaAPI with no API key
        with self.assertRaises(ValueError):
            KeepaAPI("")

    def test_check_digit_validation_integration(self):
        """Test check digit validation for barcode formats"""
        # Test valid check digits
        valid_codes = [
            "4003994155486",  # EAN-13 with valid check digit
            "036000291452",   # UPC-12 with valid check digit
            "12345670",       # EAN-8 with valid check digit
        ]

        for code in valid_codes:
            with self.subTest(code=code):
                result = detect_and_validate_identifier(code)
                self.assertTrue(result['is_valid'], f"Expected {code} to be valid")

        # Test invalid check digits
        invalid_codes = [
            "4003994155487",  # EAN-13 with wrong check digit
            "036000291453",   # UPC-12 with wrong check digit
            "12345671",       # EAN-8 with wrong check digit
        ]

        for code in invalid_codes:
            with self.subTest(code=code):
                result = detect_and_validate_identifier(code)
                self.assertFalse(result['is_valid'], f"Expected {code} to be invalid")

    @patch('PyQt6.QtCore.QThread.start')
    def test_gui_integration_mock(self, mock_start):
        """Test GUI integration with mocked QThread"""
        from gui.main_window import MainWindow
        
        # This would test the GUI if we had a proper Qt environment
        # For now, we'll test the validation logic that would be used
        
        # Test the validation function that would be called by GUI
        test_codes = ["B0BQBXBW88", "4003994155486", "invalid"]
        
        for code in test_codes:
            result = detect_and_validate_identifier(code)
            # These results would be used to update the GUI
            self.assertIn('identifier_type', result)
            self.assertIn('is_valid', result)
            self.assertIn('formatted_code', result)


class TestIdentifierUtilityFunctions(unittest.TestCase):
    """Test utility functions for identifier handling"""

    def test_product_identifier_static_methods(self):
        """Test ProductIdentifier static methods"""
        # Test normalization
        normalized = ProductIdentifier.normalize_identifier("400-399-415-5486")
        self.assertEqual(normalized, "4003994155486")

        # Test formatting
        formatted = ProductIdentifier.format_identifier("4003994155486", "EAN")
        self.assertEqual(formatted, "400 3994 15548 6")

        # Test info retrieval
        info = ProductIdentifier.get_identifier_info("ASIN")
        self.assertEqual(info['name'], "Amazon Standard Identification Number")
        self.assertEqual(info['length'], 10)

    def test_identifier_info_completeness(self):
        """Test that all supported identifiers have complete info"""
        supported_types = ["ASIN", "EAN", "UPC", "GTIN"]
        
        for identifier_type in supported_types:
            with self.subTest(identifier_type=identifier_type):
                info = ProductIdentifier.get_identifier_info(identifier_type)
                
                self.assertIn('name', info)
                self.assertIn('description', info)
                self.assertIn('example', info)
                self.assertIn('length', info)
                
                # Check that info is meaningful
                self.assertTrue(len(info['name']) > 0)
                self.assertTrue(len(info['description']) > 0)
                self.assertTrue(len(info['example']) > 0)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
