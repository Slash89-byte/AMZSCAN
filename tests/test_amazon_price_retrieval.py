"""
Comprehensive tests for Amazon Price Retrieval during Real-time Brand Scanning

This test suite ensures that the real-time scanning system properly retrieves
Amazon prices for products during brand scanning operations.
"""

import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
import time
from decimal import Decimal

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.product_matcher import ProductMatcher, QogitaProduct, MatchedProduct
from core.keepa_api import KeepaAPI
from core.enhanced_roi_calculator import EnhancedROICalculator


class TestAmazonPriceRetrieval(unittest.TestCase):
    """Test Amazon price retrieval functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create mock dependencies
        self.mock_keepa_api = Mock(spec=KeepaAPI)
        self.mock_roi_calculator = Mock(spec=EnhancedROICalculator)
        
        # Create matcher instance
        self.matcher = ProductMatcher(self.mock_keepa_api, self.mock_roi_calculator)
        
        # Test products
        self.test_products = [
            QogitaProduct(
                gtin='3600523951369',
                name='L\'Oreal Revitalift Laser X3 Day Cream',
                category='Beauty',
                brand="L'Oréal",
                wholesale_price=12.50,
                unit='piece',
                stock=45,
                suppliers=3,
                product_url='https://qogita.com/product1',
                image_url='https://qogita.com/image1.jpg'
            ),
            QogitaProduct(
                gtin='0000030080515',
                name='L\'Oreal True Match Foundation',
                category='Beauty',
                brand="L'Oréal",
                wholesale_price=8.75,
                unit='piece',
                stock=32,
                suppliers=2,
                product_url='https://qogita.com/product2',
                image_url='https://qogita.com/image2.jpg'
            )
        ]
    
    def test_amazon_price_extraction_from_keepa_csv_data(self):
        """Test Amazon price extraction from Keepa CSV data format"""
        # Mock Keepa response with CSV data (standard format)
        keepa_response = {
            'products': [{
                'asin': 'B08N5WRWNW',
                'title': 'L\'Oreal Revitalift Laser X3 Day Cream 50ml',
                'data': {
                    'csv': {
                        16: [1609459200, 2599, 1640995200, 2699],  # FBA prices over time
                        0: [1609459200, 2799, 1640995200, 2899],   # Amazon prices over time
                        1: [1609459200, 2399, 1640995200, 2499]    # Buy Box prices
                    }
                },
                'stats': {
                    'current': [2699, 2899, 2499, -1, -1, -1]  # Current prices
                }
            }]
        }
        
        self.mock_keepa_api.get_product_data.return_value = keepa_response
        
        # Extract Amazon price
        price = self.matcher._extract_amazon_price(keepa_response['products'][0])
        
        # Should prefer FBA price (26.99 EUR from 2699 cents)
        self.assertEqual(price, 26.99)
    
    def test_amazon_price_extraction_fallback_to_amazon_price(self):
        """Test fallback to Amazon price when FBA price not available"""
        # Mock Keepa response with only Amazon price
        keepa_response = {
            'products': [{
                'asin': 'B08N5WRWNW',
                'title': 'L\'Oreal Product',
                'data': {
                    'csv': {
                        0: [1609459200, 2599, 1640995200, 2699],   # Amazon prices
                        1: [1609459200, 2399, 1640995200, 2499]    # Buy Box prices
                        # No FBA prices (index 16)
                    }
                },
                'stats': {
                    'current': [2699, -1, 2499, -1, -1, -1]
                }
            }]
        }
        
        self.mock_keepa_api.get_product_data.return_value = keepa_response
        
        price = self.matcher._extract_amazon_price(keepa_response['products'][0])
        
        # Should use Amazon price (26.99 EUR from 2699 cents)
        self.assertEqual(price, 26.99)
    
    def test_amazon_price_extraction_from_stats_fallback(self):
        """Test price extraction from stats when CSV data unavailable"""
        # Mock Keepa response with only stats data
        keepa_response = {
            'products': [{
                'asin': 'B08N5WRWNW',
                'title': 'L\'Oreal Product',
                'stats': {
                    'current': [2599, -1, -1, -1, -1, -1]  # Only Amazon price available
                }
                # No CSV data
            }]
        }
        
        self.mock_keepa_api.get_product_data.return_value = keepa_response
        
        price = self.matcher._extract_amazon_price(keepa_response['products'][0])
        
        # Should use stats price (25.99 EUR from 2599 cents)
        self.assertEqual(price, 25.99)
    
    def test_amazon_price_not_available(self):
        """Test handling when Amazon price is not available"""
        # Mock Keepa response with no valid prices
        keepa_response = {
            'products': [{
                'asin': 'B08N5WRWNW',
                'title': 'L\'Oreal Product',
                'data': {
                    'csv': {
                        0: [1609459200, -1, 1640995200, -1],   # No valid Amazon prices
                        16: [1609459200, -1, 1640995200, -1]   # No valid FBA prices
                    }
                },
                'stats': {
                    'current': [-1, -1, -1, -1, -1, -1]  # No current prices
                }
            }]
        }
        
        self.mock_keepa_api.get_product_data.return_value = keepa_response
        
        price = self.matcher._extract_amazon_price(keepa_response['products'][0])
        
        # Should return None when no valid price available
        self.assertIsNone(price)
    
    def test_amazon_price_zero_handling(self):
        """Test handling of zero prices (invalid)"""
        # Mock Keepa response with zero prices
        keepa_response = {
            'products': [{
                'asin': 'B08N5WRWNW',
                'title': 'L\'Oreal Product',
                'data': {
                    'csv': {
                        16: [1609459200, 0, 1640995200, 0],    # Zero FBA prices
                        0: [1609459200, 0, 1640995200, 2599]   # One valid Amazon price
                    }
                },
                'stats': {
                    'current': [2599, 0, 0, -1, -1, -1]
                }
            }]
        }
        
        self.mock_keepa_api.get_product_data.return_value = keepa_response
        
        price = self.matcher._extract_amazon_price(keepa_response['products'][0])
        
        # Should return valid Amazon price, ignoring zero values
        self.assertEqual(price, 25.99)


class TestRealTimeScanningWithAmazonPrices(unittest.TestCase):
    """Test real-time scanning workflow with Amazon price retrieval"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_keepa_api = Mock(spec=KeepaAPI)
        self.mock_roi_calculator = Mock(spec=EnhancedROICalculator)
        self.matcher = ProductMatcher(self.mock_keepa_api, self.mock_roi_calculator)
        
        # Test product
        self.test_product = QogitaProduct(
            gtin='3600523951369',
            name='L\'Oreal Revitalift Laser X3',
            category='Beauty',
            brand="L'Oréal",
            wholesale_price=12.50,
            unit='piece',
            stock=45,
            suppliers=3,
            product_url='https://qogita.com/product',
            image_url='https://qogita.com/image.jpg'
        )
    
    def test_complete_matching_with_amazon_price_retrieval(self):
        """Test complete matching workflow including Amazon price retrieval"""
        # Mock GTIN processor
        with patch.object(self.matcher.gtin_processor, 'process_gtin') as mock_gtin:
            mock_gtin.return_value = {
                'is_valid': True,
                'normalized': '3600523951369',
                'confidence': 95,
                'search_variants': ['3600523951369', '03600523951369']
            }
            
            # Mock successful Keepa API response with price data
            keepa_response = {
                'success': True,
                'asin': 'B08N5WRWNW',
                'title': 'L\'Oreal Paris Revitalift Laser X3 Day Cream',
                'data': {
                    'csv': {
                        16: [1609459200, 2599],  # FBA price: 25.99 EUR
                        0: [1609459200, 2799]    # Amazon price: 27.99 EUR
                    }
                },
                'stats': {
                    'current': [2799, -1, 2599, -1, -1, -1]
                }
            }
            self.mock_keepa_api.get_product_data.return_value = keepa_response
            
            # Mock ROI calculation
            roi_result = {
                'profit_margin': 10.49,
                'roi_percentage': 45.2,
                'total_fees': 5.01,
                'is_profitable': True
            }
            self.mock_roi_calculator.calculate_roi.return_value = roi_result

            # Execute matching
            with patch.object(self.matcher, '_calculate_profitability') as mock_profitability:
                mock_profitability.return_value = roi_result
                result = self.matcher.match_single_product(self.test_product)            # Verify Amazon price was retrieved correctly
            self.assertIsInstance(result, MatchedProduct)
            self.assertEqual(result.match_status, 'matched')
            self.assertEqual(result.amazon_asin, 'B08N5WRWNW')
            self.assertEqual(result.amazon_price, 25.99)  # Should use FBA price
            self.assertEqual(result.profit_margin, 10.49)
            self.assertEqual(result.roi_percentage, 45.2)
            self.assertGreater(result.match_confidence, 90)
            
            # Verify API calls were made
            self.mock_keepa_api.get_product_data.assert_called()
    
    def test_matching_with_no_amazon_price_found(self):
        """Test matching when no Amazon price is found"""
        # Mock valid GTIN
        with patch.object(self.matcher.gtin_processor, 'process_gtin') as mock_gtin:
            mock_gtin.return_value = {
                'is_valid': True,
                'normalized': '3600523951369',
                'confidence': 95,
                'search_variants': ['3600523951369', '03600523951369']
            }
            
            # Mock Keepa response with no price data
            keepa_response = {
                'success': True,
                'asin': 'B08N5WRWNW',
                'title': 'L\'Oreal Product',
                'data': {
                    'csv': {
                        0: [1609459200, -1],   # No Amazon price
                        16: [1609459200, -1]   # No FBA price
                    }
                },
                'stats': {
                    'current': [-1, -1, -1, -1, -1, -1]  # No current prices
                }
            }
            self.mock_keepa_api.get_product_data.return_value = keepa_response
            
            # Execute matching
            result = self.matcher.match_single_product(self.test_product)
            
            # Should still match but with status indicating no price
            self.assertEqual(result.match_status, 'no_price')
            self.assertEqual(result.amazon_asin, 'B08N5WRWNW')
            self.assertIsNone(result.amazon_price)
            self.assertIsNone(result.profit_margin)
            self.assertIsNone(result.roi_percentage)
    
    def test_multiple_product_scanning_preserves_price_data(self):
        """Test that scanning multiple products preserves Amazon price data"""
        products = [
            QogitaProduct(
                gtin='3600523951369',
                name='Product 1',
                category='Beauty',
                brand="L'Oréal",
                wholesale_price=12.50,
                unit='piece',
                stock=45,
                suppliers=3,
                product_url='https://qogita.com/product1',
                image_url='https://qogita.com/image1.jpg'
            ),
            QogitaProduct(
                gtin='0000030080515',
                name='Product 2',
                category='Beauty',
                brand="L'Oréal",
                wholesale_price=8.75,
                unit='piece',
                stock=32,
                suppliers=2,
                product_url='https://qogita.com/product2',
                image_url='https://qogita.com/image2.jpg'
            )
        ]
        
        # Mock GTIN processor for both products
        with patch.object(self.matcher.gtin_processor, 'process_gtin') as mock_gtin:
            mock_gtin.side_effect = [
                {
                    'is_valid': True,
                    'normalized': '3600523951369',
                    'confidence': 95,
                    'search_variants': ['3600523951369', '03600523951369']
                },
                {
                    'is_valid': True,
                    'normalized': '0000030080515',
                    'confidence': 90,
                    'search_variants': ['0000030080515', '000030080515']
                }
            ]
            
            # Mock Keepa responses for both products
            keepa_responses = [
                {
                    'success': True,
                    'asin': 'B08N5WRWNW',
                    'title': 'Product 1',
                    'data': {'csv': {16: [1609459200, 2599]}},
                    'stats': {'current': [2799, -1, 2599, -1, -1, -1]}
                },
                {
                    'success': True,
                    'asin': 'B07ABC123',
                    'title': 'Product 2',
                    'data': {'csv': {16: [1609459200, 1999]}},
                    'stats': {'current': [2199, -1, 1999, -1, -1, -1]}
                }
            ]
            self.mock_keepa_api.get_product_data.side_effect = keepa_responses
            
            # Mock ROI calculations
            roi_results = [
                {
                    'profit_margin': 10.49,
                    'roi_percentage': 45.2,
                    'total_fees': 5.01
                },
                {
                    'profit_margin': 8.24,
                    'roi_percentage': 38.7,
                    'total_fees': 3.51
                }
            ]
            self.mock_roi_calculator.calculate_roi.side_effect = roi_results
            
            # Process both products
            results = []
            with patch.object(self.matcher, '_calculate_profitability') as mock_profitability:
                mock_profitability.side_effect = roi_results
                for product in products:
                    result = self.matcher.match_single_product(product)
                    results.append(result)
            
            # Verify both products have correct Amazon prices
            self.assertEqual(len(results), 2)
            
            # First product
            self.assertEqual(results[0].amazon_price, 25.99)
            self.assertEqual(results[0].amazon_asin, 'B08N5WRWNW')
            self.assertEqual(results[0].profit_margin, 10.49)
            
            # Second product
            self.assertEqual(results[1].amazon_price, 19.99)
            self.assertEqual(results[1].amazon_asin, 'B07ABC123')
            self.assertEqual(results[1].profit_margin, 8.24)


class TestAmazonPriceHandlingEdgeCases(unittest.TestCase):
    """Test edge cases in Amazon price handling"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_keepa_api = Mock(spec=KeepaAPI)
        self.mock_roi_calculator = Mock(spec=EnhancedROICalculator)
        self.matcher = ProductMatcher(self.mock_keepa_api, self.mock_roi_calculator)
    
    def test_price_format_conversion(self):
        """Test proper conversion of Keepa price format to EUR"""
        # Test various price formats
        test_cases = [
            (2599, 25.99),    # Standard price
            (999, 9.99),      # Single digit euro
            (10000, 100.00),  # Round number
            (1, 0.01),        # Minimum price
            (12345, 123.45)   # Arbitrary price
        ]
        
        for keepa_price, expected_eur in test_cases:
            keepa_data = {
                'data': {
                    'csv': {
                        16: [1609459200, keepa_price]  # FBA price
                    }
                }
            }
            
            price = self.matcher._extract_amazon_price(keepa_data)
            self.assertEqual(price, expected_eur)
    
    def test_malformed_keepa_data_handling(self):
        """Test handling of malformed Keepa data"""
        malformed_data_cases = [
            {},  # Empty data
            {'data': {}},  # Missing CSV
            {'data': {'csv': {}}},  # Empty CSV
            {'data': {'csv': {'invalid': 'data'}}},  # Invalid CSV format
            {'stats': {'current': []}},  # Empty stats
        ]
        
        for malformed_data in malformed_data_cases:
            price = self.matcher._extract_amazon_price(malformed_data)
            self.assertIsNone(price)
    
    def test_price_history_with_gaps(self):
        """Test price extraction when price history has gaps"""
        keepa_data = {
            'data': {
                'csv': {
                    16: [  # FBA price history with gaps
                        1609459200, -1,    # No price
                        1640995200, 0,     # Zero price (invalid)
                        1672531200, 2599   # Valid price: 25.99 EUR
                    ]
                }
            }
        }
        
        price = self.matcher._extract_amazon_price(keepa_data)
        
        # Should extract the latest valid price
        self.assertEqual(price, 25.99)
    
    def test_concurrent_price_extraction(self):
        """Test that price extraction works correctly under concurrent access"""
        import threading
        import queue
        
        results = queue.Queue()
        
        def extract_price(keepa_data):
            price = self.matcher._extract_amazon_price(keepa_data)
            results.put(price)
        
        # Test data
        keepa_data = {
            'data': {
                'csv': {
                    16: [1609459200, 2599]  # 25.99 EUR
                }
            }
        }
        
        # Run multiple threads
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=extract_price, args=(keepa_data,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Verify all results are correct
        while not results.empty():
            price = results.get()
            self.assertEqual(price, 25.99)


if __name__ == '__main__':
    # Run with verbose output
    unittest.main(verbosity=2)
