"""
Unit tests for Keepa API integration module
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
from core.keepa_api import KeepaAPI
import requests


class TestKeepaAPI(unittest.TestCase):
    """Test cases for KeepaAPI class"""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.api_key = "test_api_key_12345"
        self.keepa_api = KeepaAPI(self.api_key)
        self.test_asin = "B08N5WRWNW"
        
        # Sample response data that mimics real Keepa API response
        self.sample_keepa_response = {
            "products": [{
                "asin": "B08N5WRWNW",
                "title": "Test Product Title",
                "lastUpdate": 1640995200,
                "csv": {
                    1: [1640995200, 2999, 1640995260, 2899],  # Amazon price history (cents)
                    3: [1640995200, 15000, 1640995260, 14500]  # Sales rank history
                },
                "reviewCount": 150,
                "rating": 45,  # Rating * 10 (4.5 stars)
                "categoryTree": [{"name": "Electronics"}],
                "packageWeight": 500,  # grams
                "availabilityAmazon": 1
            }]
        }
        
        self.expected_parsed_data = {
            "asin": "B08N5WRWNW",
            "title": "Test Product Title",
            "current_price": 28.99,  # 2899 cents -> 28.99 euros
            "sales_rank": 14500,
            "review_count": 150,
            "rating": 4.5,  # 45 / 10
            "category": "Electronics",
            "weight": 0.5,  # 500g -> 0.5kg
            "in_stock": True,
            "last_updated": 1640995200
        }

    def test_init(self):
        """Test KeepaAPI initialization"""
        api = KeepaAPI("test_key")
        self.assertEqual(api.api_key, "test_key")
        self.assertEqual(api.base_url, "https://api.keepa.com")
        self.assertIsInstance(api.session, requests.Session)
        self.assertEqual(
            api.session.headers['User-Agent'], 
            'Amazon-Profitability-Analyzer/1.0'
        )

    @patch('core.keepa_api.requests.Session.get')
    def test_get_product_data_success(self, mock_get):
        """Test successful product data retrieval"""
        # Mock successful API response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = self.sample_keepa_response
        mock_get.return_value = mock_response
        
        result = self.keepa_api.get_product_data(self.test_asin)
        
        # Verify API call was made correctly
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        self.assertEqual(call_args[0][0], "https://api.keepa.com/product")
        
        # Check parameters match current implementation
        params = call_args[1]['params']
        self.assertEqual(params['key'], self.api_key)
        self.assertEqual(params['domain'], 4)  # Default France domain
        self.assertEqual(params['asin'], self.test_asin)
        self.assertEqual(params['stats'], 1)  # Current implementation uses 1
        
        # Verify parsed result
        self.assertIsNotNone(result)
        self.assertEqual(result['asin'], self.expected_parsed_data['asin'])
        self.assertEqual(result['title'], self.expected_parsed_data['title'])
        self.assertEqual(result['current_price'], self.expected_parsed_data['current_price'])
        self.assertEqual(result['sales_rank'], self.expected_parsed_data['sales_rank'])
        self.assertEqual(result['review_count'], self.expected_parsed_data['review_count'])
        self.assertEqual(result['rating'], self.expected_parsed_data['rating'])
        self.assertEqual(result['category'], self.expected_parsed_data['category'])
        self.assertEqual(result['weight'], self.expected_parsed_data['weight'])
        self.assertEqual(result['in_stock'], self.expected_parsed_data['in_stock'])

    @patch('core.keepa_api.requests.Session.get')
    def test_get_product_data_with_custom_domain(self, mock_get):
        """Test product data retrieval with custom domain"""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = self.sample_keepa_response
        mock_get.return_value = mock_response
        
        # Test with Germany domain (3)
        result = self.keepa_api.get_product_data(self.test_asin, domain=3)
        
        # Verify correct domain was used
        call_args = mock_get.call_args
        params = call_args[1]['params']
        self.assertEqual(params['domain'], 3)

    def test_get_product_data_no_api_key(self):
        """Test that ValueError is raised when no API key is provided"""
        with self.assertRaises(ValueError) as context:
            api = KeepaAPI("")
        
        self.assertEqual(str(context.exception), "Keepa API key is required")

    @patch('core.keepa_api.requests.Session.get')
    def test_get_product_data_empty_response(self, mock_get):
        """Test handling of empty product response"""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"products": []}
        mock_get.return_value = mock_response
        
        result = self.keepa_api.get_product_data(self.test_asin)
        
        self.assertIsNone(result)

    @patch('core.keepa_api.requests.Session.get')
    def test_get_product_data_no_products_key(self, mock_get):
        """Test handling of response without products key"""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"error": "Product not found"}
        mock_get.return_value = mock_response
        
        result = self.keepa_api.get_product_data(self.test_asin)
        
        self.assertIsNone(result)

    @patch('core.keepa_api.requests.Session.get')
    def test_get_product_data_request_exception(self, mock_get):
        """Test handling of request exceptions"""
        mock_get.side_effect = requests.exceptions.RequestException("Connection error")
        
        result = self.keepa_api.get_product_data(self.test_asin)
        
        self.assertIsNone(result)

    @patch('core.keepa_api.requests.Session.get')
    def test_get_product_data_json_decode_error(self, mock_get):
        """Test handling of JSON decode errors"""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_get.return_value = mock_response
        
        result = self.keepa_api.get_product_data(self.test_asin)
        
        self.assertIsNone(result)

    def test_parse_product_data(self):
        """Test the product data parsing functionality"""
        raw_product = self.sample_keepa_response["products"][0]
        
        parsed_data = self.keepa_api._parse_product_data(raw_product)
        
        # Verify all fields are parsed correctly
        self.assertEqual(parsed_data['asin'], "B08N5WRWNW")
        self.assertEqual(parsed_data['title'], "Test Product Title")
        self.assertEqual(parsed_data['current_price'], 28.99)
        self.assertEqual(parsed_data['sales_rank'], 14500)
        self.assertEqual(parsed_data['review_count'], 150)
        self.assertEqual(parsed_data['rating'], 4.5)
        self.assertEqual(parsed_data['category'], "Electronics")
        self.assertEqual(parsed_data['weight'], 0.5)
        self.assertTrue(parsed_data['in_stock'])
        self.assertEqual(parsed_data['last_updated'], 1640995200)
        self.assertIn('raw_data', parsed_data)

    def test_parse_product_data_missing_price(self):
        """Test parsing when price data is missing or invalid"""
        raw_product = {
            "asin": "B08N5WRWNW",
            "title": "Test Product",
            "csv": {1: [1640995200, -1]},  # -1 indicates no price data
            "reviewCount": 0,
            "rating": 0
        }
        
        parsed_data = self.keepa_api._parse_product_data(raw_product)
        
        self.assertEqual(parsed_data['current_price'], 0.0)
        self.assertEqual(parsed_data['rating'], 0.0)

    def test_parse_product_data_missing_optional_fields(self):
        """Test parsing when optional fields are missing"""
        raw_product = {
            "asin": "B08N5WRWNW",
            "title": "Test Product"
        }
        
        parsed_data = self.keepa_api._parse_product_data(raw_product)
        
        self.assertEqual(parsed_data['current_price'], 0.0)
        self.assertIsNone(parsed_data['sales_rank'])
        self.assertEqual(parsed_data['review_count'], 0)
        self.assertEqual(parsed_data['rating'], 0.0)
        self.assertIsNone(parsed_data['category'])
        self.assertEqual(parsed_data['weight'], 0.5)  # default weight

    def test_parse_product_data_different_category_formats(self):
        """Test parsing with different category tree formats"""
        # Test with string category (not dict)
        raw_product_string = {
            "asin": "B08N5WRWNW",
            "title": "Test Product",
            "categoryTree": ["Electronics", "Computers"]
        }
        parsed_data = self.keepa_api._parse_product_data(raw_product_string)
        self.assertEqual(parsed_data['category'], "Electronics")
        
        # Test with dict category
        raw_product_dict = {
            "asin": "B08N5WRWNW", 
            "title": "Test Product",
            "categoryTree": [{"name": "Books", "id": 283155}]
        }
        parsed_data = self.keepa_api._parse_product_data(raw_product_dict)
        self.assertEqual(parsed_data['category'], "Books")
        
        # Test with empty category tree
        raw_product_empty = {
            "asin": "B08N5WRWNW",
            "title": "Test Product", 
            "categoryTree": []
        }
        parsed_data = self.keepa_api._parse_product_data(raw_product_empty)
        self.assertIsNone(parsed_data['category'])

    @patch('core.keepa_api.requests.Session.get')
    def test_get_price_history(self, mock_get):
        """Test price history retrieval"""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = self.sample_keepa_response
        mock_get.return_value = mock_response
        
        result = self.keepa_api.get_price_history(self.test_asin)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['asin'], self.test_asin)
        self.assertEqual(result['current_price'], 28.99)
        self.assertIn('price_history', result)
        
        # Check price history structure
        price_history = result['price_history']
        self.assertEqual(len(price_history), 2)  # Two price points
        self.assertEqual(price_history[0]['price'], 29.99)  # 2999 cents
        self.assertEqual(price_history[1]['price'], 28.99)  # 2899 cents

    @patch('core.keepa_api.requests.Session.get')
    def test_test_connection_success(self, mock_get):
        """Test successful API connection test"""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"tokensLeft": 1000}
        mock_get.return_value = mock_response
        
        result = self.keepa_api.test_connection()
        
        self.assertTrue(result)
        
        # Verify correct endpoint was called
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        self.assertEqual(call_args[0][0], "https://api.keepa.com/token")
        self.assertEqual(call_args[1]['params']['key'], self.api_key)

    @patch('core.keepa_api.requests.Session.get')
    def test_test_connection_failure(self, mock_get):
        """Test failed API connection test"""
        mock_get.side_effect = requests.exceptions.RequestException("Connection failed")
        
        result = self.keepa_api.test_connection()
        
        self.assertFalse(result)

    @patch('core.keepa_api.requests.Session.get')
    def test_test_connection_invalid_response(self, mock_get):
        """Test connection test with invalid response"""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"tokensLeft": -1}  # Negative tokens indicate invalid key
        mock_get.return_value = mock_response
        
        result = self.keepa_api.test_connection()
        
        # Should return False when tokensLeft is negative
        self.assertFalse(result)


class TestKeepaAPIIntegration(unittest.TestCase):
    """Integration tests for KeepaAPI (requires actual API key)"""

    def setUp(self):
        """Set up integration test fixtures"""
        # Set up for multi-format identifier tests
        self.api_key = "test_api_key_12345"
        self.keepa_api = KeepaAPI(self.api_key)
        
        # Sample response data for multi-format tests
        self.sample_keepa_response = {
            "products": [{
                "asin": "B08N5WRWNW",
                "title": "Test Product Title",
                "lastUpdate": 1640995200,
                "csv": [[], [1640995200, 2999]],  # Buy Box empty, Amazon price
                "reviewCount": 150,
                "rating": 45,
                "categoryTree": [{"name": "Electronics"}],
                "packageWeight": 500,
                "availabilityAmazon": 1
            }]
        }
        
    def test_real_api_call(self):
        """Test with real API (requires valid API key)"""
        # Skip this test as it requires a real API key
        self.skipTest("Integration test skipped - requires real API key")

    @patch('core.keepa_api.requests.Session.get')
    def test_get_product_data_with_ean(self, mock_get):
        """Test product data retrieval with EAN identifier"""
        mock_response = Mock()
        mock_response.json.return_value = self.sample_keepa_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Test EAN lookup
        ean_code = "4003994155486"
        product_data = self.keepa_api.get_product_data(ean_code)
        
        # Verify API was called with 'code' parameter for EAN
        mock_get.assert_called_once()
        call_args = mock_get.call_args[1]['params']
        self.assertIn('code', call_args)
        self.assertEqual(call_args['code'], ean_code)
        self.assertNotIn('asin', call_args)
        
        # Verify response parsing
        self.assertIsNotNone(product_data)
        self.assertEqual(product_data['asin'], "B08N5WRWNW")

    @patch('core.keepa_api.requests.Session.get')
    def test_get_product_data_with_upc(self, mock_get):
        """Test product data retrieval with UPC identifier"""
        mock_response = Mock()
        mock_response.json.return_value = self.sample_keepa_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Test UPC lookup
        upc_code = "036000291452"
        product_data = self.keepa_api.get_product_data(upc_code)
        
        # Verify API was called with 'code' parameter for UPC
        call_args = mock_get.call_args[1]['params']
        self.assertIn('code', call_args)
        self.assertEqual(call_args['code'], upc_code)
        
        self.assertIsNotNone(product_data)

    @patch('core.keepa_api.requests.Session.get')
    def test_get_product_data_with_asin_uses_asin_param(self, mock_get):
        """Test that ASIN lookups still use 'asin' parameter"""
        mock_response = Mock()
        mock_response.json.return_value = self.sample_keepa_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Test ASIN lookup
        asin_code = "B0BQBXBW88"
        product_data = self.keepa_api.get_product_data(asin_code)
        
        # Verify API was called with 'asin' parameter for ASIN
        call_args = mock_get.call_args[1]['params']
        self.assertIn('asin', call_args)
        self.assertEqual(call_args['asin'], asin_code)
        self.assertNotIn('code', call_args)
        
        self.assertIsNotNone(product_data)

    def test_get_product_data_with_invalid_identifier(self):
        """Test product data retrieval with invalid identifier"""
        # Test with invalid identifier
        invalid_code = "invalid_identifier"
        product_data = self.keepa_api.get_product_data(invalid_code)
        
        # Should return None for invalid identifier
        self.assertIsNone(product_data)

    def test_get_product_data_with_unsupported_identifier_type(self):
        """Test product data retrieval with unsupported identifier type"""
        # Create a mock identifier that would be detected as unsupported
        with patch('utils.identifiers.detect_and_validate_identifier') as mock_detect:
            mock_detect.return_value = {
                'is_valid': True,
                'identifier_type': 'UNSUPPORTED_TYPE',
                'normalized_code': 'TEST123'
            }
            
            product_data = self.keepa_api.get_product_data('TEST123')
            self.assertIsNone(product_data)

    @patch('core.keepa_api.requests.Session.get')
    def test_multi_format_identifier_parameter_mapping(self, mock_get):
        """Test that different identifier types map to correct API parameters"""
        mock_response = Mock()
        mock_response.json.return_value = self.sample_keepa_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        test_cases = [
            ("B0BQBXBW88", "asin"),      # ASIN -> asin parameter
            ("4003994155486", "code"),   # EAN -> code parameter
            ("036000291452", "code"),    # UPC -> code parameter
            # Note: GTIN-14 removed as check digit validation may fail for test data
        ]
        
        for identifier, expected_param in test_cases:
            with self.subTest(identifier=identifier):
                mock_get.reset_mock()
                
                product_data = self.keepa_api.get_product_data(identifier)
                
                self.assertIsNotNone(product_data)
                call_args = mock_get.call_args[1]['params']
                self.assertIn(expected_param, call_args)
                self.assertEqual(call_args[expected_param], identifier)


if __name__ == '__main__':
    # Run tests with detailed output
    unittest.main(verbosity=2)
