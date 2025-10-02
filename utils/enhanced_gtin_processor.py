"""
Enhanced GTIN Processing and Validation

This module provides comprehensive GTIN validation, normalization, and processing
specifically designed for Qogita-to-Amazon product matching.
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Union


class EnhancedGTINProcessor:
    """Enhanced GTIN processing with comprehensive validation and normalization"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def process_gtin(self, raw_gtin: Union[str, int]) -> Dict:
        """
        Process and validate a GTIN from Qogita data
        
        Args:
            raw_gtin: Raw GTIN value from Qogita (string or int)
            
        Returns:
            Dictionary with processing results:
            {
                'original': original value,
                'normalized': standardized GTIN,
                'format': GTIN format (GTIN-8, GTIN-12, GTIN-13, GTIN-14),
                'is_valid': boolean validation result,
                'check_digit_valid': boolean checksum validation,
                'search_variants': list of search variants to try,
                'confidence': confidence level (0-100)
            }
        """
        result = {
            'original': str(raw_gtin),
            'normalized': None,
            'format': None,
            'is_valid': False,
            'check_digit_valid': False,
            'search_variants': [],
            'confidence': 0
        }
        
        try:
            # Convert to string and clean
            gtin_str = str(raw_gtin).strip()
            
            # Remove any non-digit characters
            digits_only = re.sub(r'\D', '', gtin_str)
            
            if not digits_only:
                return result
            
            # Determine format and validate
            length = len(digits_only)
            
            if length == 8:
                result.update(self._process_gtin8(digits_only))
            elif length == 12:
                result.update(self._process_gtin12(digits_only))
            elif length == 13:
                result.update(self._process_gtin13(digits_only))
            elif length == 14:
                result.update(self._process_gtin14(digits_only))
            elif length < 8:
                # Try padding with zeros
                padded = digits_only.zfill(12)  # Pad to UPC length
                result.update(self._process_gtin12(padded))
                result['confidence'] = max(0, result['confidence'] - 20)  # Lower confidence for padded
            elif length > 14:
                # Try truncating or extracting
                # Some systems prefix with additional digits
                if length <= 18:
                    # Try last 14, 13, or 12 digits
                    for extract_length in [14, 13, 12]:
                        extracted = digits_only[-extract_length:]
                        test_result = self.process_gtin(extracted)
                        if test_result['is_valid']:
                            result.update(test_result)
                            result['confidence'] = max(0, result['confidence'] - 10)
                            break
            
            # Generate search variants
            if result['normalized']:
                result['search_variants'] = self._generate_search_variants(result['normalized'])
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing GTIN {raw_gtin}: {str(e)}")
            return result
    
    def _process_gtin8(self, digits: str) -> Dict:
        """Process GTIN-8 (EAN-8)"""
        is_valid = self._validate_checksum(digits)
        return {
            'normalized': digits,
            'format': 'GTIN-8',
            'is_valid': is_valid,
            'check_digit_valid': is_valid,
            'confidence': 85 if is_valid else 30
        }
    
    def _process_gtin12(self, digits: str) -> Dict:
        """Process GTIN-12 (UPC-A)"""
        is_valid = self._validate_checksum(digits)
        
        # Convert UPC to EAN-13 by prefixing with 0
        ean13 = '0' + digits
        ean13_valid = self._validate_checksum(ean13)
        
        return {
            'normalized': digits,
            'format': 'GTIN-12',
            'is_valid': is_valid,
            'check_digit_valid': is_valid,
            'confidence': 90 if is_valid else 40,
            'ean13_equivalent': ean13 if ean13_valid else None
        }
    
    def _process_gtin13(self, digits: str) -> Dict:
        """Process GTIN-13 (EAN-13)"""
        is_valid = self._validate_checksum(digits)
        
        # Check if it's a UPC with leading zero
        upc_equivalent = None
        if digits.startswith('0'):
            upc_candidate = digits[1:]
            if self._validate_checksum(upc_candidate):
                upc_equivalent = upc_candidate
        
        return {
            'normalized': digits,
            'format': 'GTIN-13',
            'is_valid': is_valid,
            'check_digit_valid': is_valid,
            'confidence': 95 if is_valid else 50,
            'upc_equivalent': upc_equivalent
        }
    
    def _process_gtin14(self, digits: str) -> Dict:
        """Process GTIN-14"""
        is_valid = self._validate_checksum(digits)
        
        # Extract base GTIN-13 (remove packaging indicator)
        base_gtin13 = digits[1:]
        base_valid = self._validate_checksum(base_gtin13)
        
        return {
            'normalized': digits,
            'format': 'GTIN-14',
            'is_valid': is_valid,
            'check_digit_valid': is_valid,
            'confidence': 80 if is_valid else 35,
            'base_gtin13': base_gtin13 if base_valid else None,
            'packaging_indicator': digits[0]
        }
    
    def _validate_checksum(self, digits: str) -> bool:
        """Validate GTIN checksum using modulo 10 algorithm"""
        if not digits or not digits.isdigit():
            return False
        
        try:
            # Calculate checksum
            total = 0
            for i, digit in enumerate(digits[:-1]):
                weight = 3 if i % 2 == (len(digits) % 2) else 1
                total += int(digit) * weight
            
            calculated_check = (10 - (total % 10)) % 10
            actual_check = int(digits[-1])
            
            return calculated_check == actual_check
            
        except (ValueError, IndexError):
            return False
    
    def _generate_search_variants(self, normalized_gtin: str) -> List[str]:
        """Generate different variants of GTIN for searching"""
        variants = [normalized_gtin]
        
        length = len(normalized_gtin)
        
        if length == 12:
            # UPC to EAN-13
            ean13 = '0' + normalized_gtin
            if self._validate_checksum(ean13):
                variants.append(ean13)
        
        elif length == 13:
            # EAN-13 to UPC (if starts with 0)
            if normalized_gtin.startswith('0'):
                upc = normalized_gtin[1:]
                if self._validate_checksum(upc):
                    variants.append(upc)
            
            # For EAN-13, don't generate GTIN-14 variants as they're often invalid
            # Focus on the original EAN-13 and any valid UPC conversion
        
        elif length == 14:
            # GTIN-14 to base GTIN-13 (remove indicator digit)
            base_gtin13 = normalized_gtin[1:]
            if self._validate_checksum(base_gtin13):
                variants.append(base_gtin13)
        
        return list(set(variants))  # Remove duplicates
    
    def _calculate_check_digit(self, digits_without_check: str) -> int:
        """Calculate check digit for GTIN"""
        total = 0
        for i, digit in enumerate(digits_without_check):
            weight = 3 if i % 2 == (len(digits_without_check) % 2) else 1
            total += int(digit) * weight
        
        return (10 - (total % 10)) % 10
    
    def find_best_gtin_for_amazon(self, gtin_data: Dict) -> Optional[str]:
        """
        Find the best GTIN variant for Amazon search
        
        Args:
            gtin_data: Result from process_gtin()
            
        Returns:
            Best GTIN variant for Amazon search, or None if invalid
        """
        if not gtin_data['is_valid']:
            return None
        
        # Amazon preference order:
        # 1. GTIN-13 (EAN-13) - most common internationally
        # 2. GTIN-12 (UPC-A) - common in US
        # 3. GTIN-14 - for cases
        # 4. GTIN-8 - rare but supported
        
        normalized = gtin_data['normalized']
        variants = gtin_data['search_variants']
        
        # Prefer EAN-13 format
        for variant in variants:
            if len(variant) == 13 and self._validate_checksum(variant):
                return variant
        
        # Then UPC-12
        for variant in variants:
            if len(variant) == 12 and self._validate_checksum(variant):
                return variant
        
        # Fall back to original normalized
        return normalized


class QogitaGTINAnalyzer:
    """Analyzer for GTIN patterns in Qogita data"""
    
    def __init__(self):
        self.processor = EnhancedGTINProcessor()
        self.logger = logging.getLogger(__name__)
    
    def analyze_brand_gtins(self, products: List[Dict]) -> Dict:
        """
        Analyze GTIN quality across a brand's products
        
        Args:
            products: List of Qogita product dictionaries
            
        Returns:
            Analysis results with statistics and recommendations
        """
        analysis = {
            'total_products': len(products),
            'gtin_stats': {
                'valid_gtins': 0,
                'invalid_gtins': 0,
                'missing_gtins': 0,
                'format_distribution': {},
                'confidence_distribution': {}
            },
            'searchable_products': 0,
            'recommendations': []
        }
        
        valid_gtins = []
        
        for product in products:
            gtin = product.get('gtin', '')
            
            if not gtin:
                analysis['gtin_stats']['missing_gtins'] += 1
                continue
            
            result = self.processor.process_gtin(gtin)
            
            if result['is_valid']:
                analysis['gtin_stats']['valid_gtins'] += 1
                valid_gtins.append(result)
                
                # Track format distribution
                format_type = result['format']
                analysis['gtin_stats']['format_distribution'][format_type] = \
                    analysis['gtin_stats']['format_distribution'].get(format_type, 0) + 1
                
                # Track confidence distribution
                confidence = result['confidence']
                if confidence >= 90:
                    range_key = '90-100%'
                elif confidence >= 70:
                    range_key = '70-89%'
                elif confidence >= 50:
                    range_key = '50-69%'
                else:
                    range_key = '<50%'
                
                analysis['gtin_stats']['confidence_distribution'][range_key] = \
                    analysis['gtin_stats']['confidence_distribution'].get(range_key, 0) + 1
                
                if confidence >= 70:
                    analysis['searchable_products'] += 1
            else:
                analysis['gtin_stats']['invalid_gtins'] += 1
        
        # Generate recommendations
        total = analysis['total_products']
        valid_rate = analysis['gtin_stats']['valid_gtins'] / total if total > 0 else 0
        searchable_rate = analysis['searchable_products'] / total if total > 0 else 0
        
        if valid_rate < 0.5:
            analysis['recommendations'].append(
                "Low GTIN validity rate. Consider alternative matching strategies."
            )
        
        if searchable_rate >= 0.8:
            analysis['recommendations'].append(
                "Excellent GTIN coverage. Amazon matching should work well."
            )
        elif searchable_rate >= 0.6:
            analysis['recommendations'].append(
                "Good GTIN coverage. Most products should match on Amazon."
            )
        else:
            analysis['recommendations'].append(
                "Moderate GTIN coverage. Implement fallback matching strategies."
            )
        
        return analysis


# Usage example and testing functions
def test_gtin_processing():
    """Test the enhanced GTIN processing"""
    processor = EnhancedGTINProcessor()
    
    test_gtins = [
        "0000030080515",  # L'Oréal product from our Qogita data
        "0000030080539", 
        "0000030093669",
        "123456789012",   # Standard UPC
        "1234567890123",  # Standard EAN-13
        "12345678901234", # GTIN-14
        "12345678",       # EAN-8
        "0123456789",     # Short, needs padding
        "invalid",        # Invalid
        ""                # Empty
    ]
    
    print("🧪 Testing Enhanced GTIN Processing")
    print("=" * 50)
    
    for gtin in test_gtins:
        result = processor.process_gtin(gtin)
        print(f"\nGTIN: {gtin}")
        print(f"  Valid: {result['is_valid']}")
        print(f"  Format: {result['format']}")
        print(f"  Normalized: {result['normalized']}")
        print(f"  Confidence: {result['confidence']}%")
        print(f"  Variants: {result['search_variants']}")
        
        if result['is_valid']:
            best = processor.find_best_gtin_for_amazon(result)
            print(f"  Best for Amazon: {best}")


if __name__ == "__main__":
    test_gtin_processing()
