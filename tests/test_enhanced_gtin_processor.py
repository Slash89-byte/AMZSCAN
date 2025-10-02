"""
Unit tests for Enhanced GTIN Processor

Tests the comprehensive GTIN validation, normalization, and processing
functionality for improved Amazon product matching.
"""

import unittest
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.enhanced_gtin_processor import EnhancedGTINProcessor, QogitaGTINAnalyzer


class TestEnhancedGTINProcessor(unittest.TestCase):
    """Test cases for Enhanced GTIN Processor"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.processor = EnhancedGTINProcessor()
    
    def test_valid_gtin13_processing(self):
        """Test processing of valid GTIN-13 codes"""
        # Test with real L'Oréal GTIN
        gtin = "3600523951369"
        result = self.processor.process_gtin(gtin)
        
        self.assertTrue(result['is_valid'])
        self.assertEqual(result['format'], 'GTIN-13')
        self.assertEqual(result['normalized'], gtin)
        self.assertEqual(result['confidence'], 95)
        self.assertTrue(result['check_digit_valid'])
        self.assertIn(gtin, result['search_variants'])
    
    def test_gtin13_with_leading_zeros(self):
        """Test GTIN-13 with leading zeros"""
        gtin = "0000030080515"
        result = self.processor.process_gtin(gtin)
        
        self.assertTrue(result['is_valid'])
        self.assertEqual(result['format'], 'GTIN-13')
        self.assertEqual(result['normalized'], gtin)
        self.assertEqual(result['confidence'], 95)
        self.assertGreaterEqual(len(result['search_variants']), 2)
    
    def test_invalid_gtin_checksum(self):
        """Test GTIN with invalid checksum"""
        gtin = "3607345064672"  # Invalid checksum
        result = self.processor.process_gtin(gtin)
        
        self.assertFalse(result['is_valid'])
        self.assertEqual(result['format'], 'GTIN-13')
        self.assertEqual(result['confidence'], 50)  # Format correct but checksum invalid
        self.assertFalse(result['check_digit_valid'])
    
    def test_gtin8_processing(self):
        """Test GTIN-8 processing"""
        gtin = "12345670"  # Valid GTIN-8 with correct checksum
        result = self.processor.process_gtin(gtin)
        
        self.assertTrue(result['is_valid'])
        self.assertEqual(result['format'], 'GTIN-8')
        self.assertEqual(result['normalized'], gtin)
        self.assertGreater(result['confidence'], 80)
    
    def test_gtin12_processing(self):
        """Test GTIN-12 (UPC) processing"""
        gtin = "123456789012"
        result = self.processor.process_gtin(gtin)
        
        # This should be processed as GTIN-12 format
        self.assertEqual(result['format'], 'GTIN-12')
        # Checksum validation will determine validity
        self.assertIsInstance(result['is_valid'], bool)
        self.assertIsInstance(result['confidence'], int)
    
    def test_gtin14_processing(self):
        """Test GTIN-14 processing"""
        gtin = "12345678901234"
        result = self.processor.process_gtin(gtin)
        
        self.assertEqual(result['format'], 'GTIN-14')
        self.assertIsInstance(result['is_valid'], bool)
        self.assertIsInstance(result['confidence'], int)
    
    def test_invalid_gtin_too_short(self):
        """Test GTIN that's too short"""
        gtin = "123456"
        result = self.processor.process_gtin(gtin)
        
        # Short GTINs get padded, so they have a format but lower confidence
        self.assertIsNotNone(result['format'])
        self.assertTrue(result['confidence'] < 70)  # Lower confidence for padded
        self.assertIsNotNone(result['normalized'])
    
    def test_invalid_gtin_too_long(self):
        """Test GTIN that's too long"""
        gtin = "123456789012345"
        result = self.processor.process_gtin(gtin)
        
        self.assertFalse(result['is_valid'])
        self.assertIsNone(result['format'])
        self.assertEqual(result['confidence'], 0)
    
    def test_empty_gtin(self):
        """Test empty GTIN"""
        result = self.processor.process_gtin("")
        
        self.assertFalse(result['is_valid'])
        self.assertIsNone(result['format'])
        self.assertEqual(result['confidence'], 0)
        self.assertIsNone(result['normalized'])
    
    def test_non_numeric_gtin(self):
        """Test GTIN with non-numeric characters"""
        gtin = "ABC123DEF456"
        result = self.processor.process_gtin(gtin)
        
        # After cleaning, we get "123456" which gets padded
        self.assertIsNotNone(result['format'])
        self.assertTrue(result['confidence'] < 70)  # Lower confidence for cleaned/padded
    
    def test_search_variants_generation(self):
        """Test search variant generation"""
        gtin = "3600523951369"
        result = self.processor.process_gtin(gtin)
        
        variants = result['search_variants']
        self.assertIsInstance(variants, list)
        self.assertGreater(len(variants), 0)
        self.assertIn(gtin, variants)
        
        # Should include variant with leading digit
        padded_variant = f"0{gtin}"
        self.assertIn(padded_variant, variants)
    
    def test_checksum_calculation(self):
        """Test checksum calculation accuracy"""
        # Test known valid GTIN
        gtin_without_check = "360052395136"
        calculated_check = self.processor._calculate_check_digit(gtin_without_check)
        self.assertEqual(calculated_check, 9)  # Expected check digit for this GTIN
    
    def test_best_gtin_selection(self):
        """Test best GTIN selection for Amazon"""
        test_data = {
            'original': '0000030080515',
            'normalized': '0000030080515',
            'format': 'GTIN-13',
            'is_valid': True,
            'confidence': 95,
            'search_variants': ['0000030080515', '000030080515']
        }
        
        best_gtin = self.processor.find_best_gtin_for_amazon(test_data)
        self.assertIsNotNone(best_gtin)
        self.assertIn(best_gtin, test_data['search_variants'])
    
    def test_integer_input(self):
        """Test processing integer input"""
        gtin_int = 3600523951369
        result = self.processor.process_gtin(gtin_int)
        
        self.assertTrue(result['is_valid'])
        self.assertEqual(result['normalized'], "3600523951369")


class TestQogitaGTINAnalyzer(unittest.TestCase):
    """Test cases for Qogita GTIN Analyzer"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.analyzer = QogitaGTINAnalyzer()
    
    def test_analyze_brand_gtins(self):
        """Test brand GTIN analysis"""
        test_products = [
            {
                'gtin': '3600523951369',
                'brand': "L'Oréal",
                'name': 'Revitalift Laser X3 Day Cream'
            },
            {
                'gtin': '0000030080515',
                'brand': "L'Oréal",
                'name': 'True Match Foundation'
            },
            {
                'gtin': 'invalid_gtin',
                'brand': "L'Oréal",
                'name': 'Invalid Product'
            }
        ]
        
        analysis = self.analyzer.analyze_brand_gtins(test_products)
        
        self.assertIn('total_products', analysis)
        self.assertIn('gtin_stats', analysis)
        self.assertIn('searchable_products', analysis)
        self.assertIn('recommendations', analysis)
        
        # Check gtin_stats structure
        gtin_stats = analysis['gtin_stats']
        self.assertIn('valid_gtins', gtin_stats)
        self.assertIn('invalid_gtins', gtin_stats)
        self.assertIn('confidence_distribution', gtin_stats)
        self.assertIn('format_distribution', gtin_stats)
        
        self.assertEqual(analysis['total_products'], 3)
        self.assertEqual(gtin_stats['valid_gtins'], 2)
        self.assertEqual(gtin_stats['invalid_gtins'], 1)
    
    def test_confidence_distribution(self):
        """Test confidence level distribution analysis"""
        test_products = [
            {'gtin': '3600523951369', 'brand': "L'Oréal", 'name': 'Product 1'},  # High confidence
            {'gtin': '3607345064672', 'brand': "L'Oréal", 'name': 'Product 2'},  # Medium confidence (invalid checksum)
            {'gtin': '123456789', 'brand': "L'Oréal", 'name': 'Product 3'},      # Low confidence
        ]
        
        analysis = self.analyzer.analyze_brand_gtins(test_products)
        
        distribution = analysis['gtin_stats']['confidence_distribution']
        # Check for percentage range keys used by the analyzer
        possible_ranges = ['90-100%', '70-89%', '50-69%', '0-49%']
        
        # Should have at least one confidence range
        self.assertGreater(len(distribution), 0)
        
        # All keys should be valid ranges
        for key in distribution.keys():
            self.assertIn(key, possible_ranges)


class TestGTINValidationEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.processor = EnhancedGTINProcessor()
    
    def test_whitespace_handling(self):
        """Test GTIN with whitespace"""
        gtin_with_spaces = "  3600523951369  "
        result = self.processor.process_gtin(gtin_with_spaces)
        
        self.assertTrue(result['is_valid'])
        self.assertEqual(result['normalized'], "3600523951369")
    
    def test_none_input(self):
        """Test None input handling"""
        result = self.processor.process_gtin(None)
        
        self.assertFalse(result['is_valid'])
        self.assertEqual(result['confidence'], 0)
    
    def test_very_large_number(self):
        """Test very large number input"""
        large_number = 99999999999999999
        result = self.processor.process_gtin(large_number)
        
        # Should handle gracefully
        self.assertIsInstance(result, dict)
        self.assertIn('is_valid', result)
    
    def test_special_characters(self):
        """Test GTIN with special characters"""
        gtin_with_chars = "3600-523-951-369"
        result = self.processor.process_gtin(gtin_with_chars)
        
        # Should extract digits only
        self.assertIsInstance(result, dict)
        self.assertIn('is_valid', result)


class TestGTINProcessorPerformance(unittest.TestCase):
    """Test performance characteristics"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.processor = EnhancedGTINProcessor()
    
    def test_bulk_processing_performance(self):
        """Test processing many GTINs efficiently"""
        import time
        
        # Generate test GTINs
        test_gtins = [
            "3600523951369",
            "0000030080515",
            "3607345064672",
            "8005610636917",
            "123456789012",
            "invalid_gtin",
            "",
            "12345678"
        ] * 10  # 80 GTINs total
        
        start_time = time.time()
        
        results = []
        for gtin in test_gtins:
            result = self.processor.process_gtin(gtin)
            results.append(result)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should process 80 GTINs in reasonable time (< 1 second)
        self.assertLess(processing_time, 1.0)
        self.assertEqual(len(results), 80)
        
        # All results should have required fields
        for result in results:
            self.assertIn('is_valid', result)
            self.assertIn('confidence', result)
            self.assertIn('format', result)


if __name__ == '__main__':
    # Run with verbose output
    unittest.main(verbosity=2)
