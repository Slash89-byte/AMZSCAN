"""
Test our fee calculations against real Keepa data
"""

import unittest
from core.amazon_fees import AmazonFeesCalculator
from core.keepa_api import KeepaAPI

class TestRealDataAlignment(unittest.TestCase):
    """Test that our calculations align with real Keepa data"""
    
    def setUp(self):
        self.fees_calc = AmazonFeesCalculator('france')
    
    def test_beauty_product_fees_b0d8l8hywm(self):
        """Test fees calculation for the NIVEA product (B0D8L8HYWM)"""
        # Real data from Keepa CSV
        price = 4.72
        weight_kg = 0.43
        category = 'beauty'
        
        # Expected fees from Keepa
        expected_referral_pct = 8.05
        expected_fba_fee = 4.31
        expected_total = 4.69
        
        # Our calculations
        referral_fee = self.fees_calc.calculate_referral_fee(price, category)
        fba_fee = self.fees_calc.calculate_fba_fee(weight_kg)
        total = self.fees_calc.calculate_fees(price, weight_kg, category)
        
        # Check referral fee percentage (should be close to 8.05%)
        referral_pct = (referral_fee / price) * 100
        self.assertAlmostEqual(referral_pct, expected_referral_pct, delta=0.1)
        
        # Check FBA fee (should be close to €4.31)
        self.assertAlmostEqual(fba_fee, expected_fba_fee, delta=0.05)
        
        # Check total fees (should be close to €4.69)
        self.assertAlmostEqual(total, expected_total, delta=0.05)
    
    def test_category_mapping(self):
        """Test that French beauty categories map correctly"""
        keepa_api = KeepaAPI("dummy_key")  # Just for testing category mapping
        
        # Test various French beauty category names
        test_cases = [
            ("Beauté et Parfum", "beauty"),
            ("beauté", "beauty"),
            ("Beauty", "beauty"),
            ("Cosmetics", "beauty"),
            ("Electronics", "electronics"),
            ("Unknown Category", "default"),
            ("", "default"),
            (None, "default")
        ]
        
        for input_category, expected_output in test_cases:
            with self.subTest(input_category=input_category):
                result = keepa_api._get_fee_category(input_category)
                self.assertEqual(result, expected_output)

if __name__ == '__main__':
    unittest.main()
