"""
Product identifier utilities for detecting and validating ASIN, GTIN, EAN, UPC codes
"""

import re
from typing import Tuple, Optional


class ProductIdentifier:
    """Utility class for product identifier detection and validation"""
    
    @staticmethod
    def identify_product_code(code: str) -> Tuple[str, bool]:
        """
        Identify the type of product code and validate it
        
        Args:
            code: The product code to identify
            
        Returns:
            Tuple of (identifier_type, is_valid)
            identifier_type: "ASIN", "GTIN", "EAN", "UPC", or "UNKNOWN"
            is_valid: Boolean indicating if the identifier is valid
        """
        if not code:
            return "UNKNOWN", False
            
        code = code.strip().upper()
        
        # ASIN: 10 characters, starts with B, alphanumeric
        if ProductIdentifier._is_asin(code):
            return "ASIN", ProductIdentifier._validate_asin(code)
        
        # Remove any non-digits for barcode validation
        digits_only = ''.join(filter(str.isdigit, code))
        
        # GTIN-14 (14 digits)
        if len(digits_only) == 14:
            return "GTIN", ProductIdentifier._validate_check_digit(digits_only)
        
        # GTIN-13/EAN-13 (13 digits)
        if len(digits_only) == 13:
            return "EAN", ProductIdentifier._validate_check_digit(digits_only)
        
        # GTIN-12/UPC-A (12 digits)
        if len(digits_only) == 12:
            return "UPC", ProductIdentifier._validate_check_digit(digits_only)
        
        # GTIN-8/EAN-8 (8 digits)
        if len(digits_only) == 8:
            return "EAN", ProductIdentifier._validate_check_digit(digits_only)
        
        return "UNKNOWN", False
    
    @staticmethod
    def _is_asin(code: str) -> bool:
        """Check if code matches ASIN pattern"""
        return (len(code) == 10 and 
                code.startswith('B') and 
                code.isalnum())
    
    @staticmethod
    def _validate_asin(asin: str) -> bool:
        """Validate ASIN format"""
        if not ProductIdentifier._is_asin(asin):
            return False
        
        # Additional ASIN validation rules
        # Must contain at least one digit and one letter after 'B'
        remaining = asin[1:]  # Remove the 'B'
        has_digit = any(c.isdigit() for c in remaining)
        has_letter = any(c.isalpha() for c in remaining)
        
        return has_digit and has_letter
    
    @staticmethod
    def _validate_check_digit(code: str) -> bool:
        """
        Validate check digit for GTIN/EAN/UPC codes using standard algorithm
        """
        if not code.isdigit() or len(code) < 8:
            return False
        
        digits = [int(d) for d in code]
        
        # Calculate check digit using standard GTIN algorithm
        # Multiply odd position digits by 1, even position by 3
        # (counting from right, starting at 1)
        total = 0
        for i, digit in enumerate(reversed(digits[:-1])):
            multiplier = 3 if i % 2 == 0 else 1
            total += digit * multiplier
        
        # Check digit is what makes total divisible by 10
        calculated_check = (10 - (total % 10)) % 10
        actual_check = digits[-1]
        
        return calculated_check == actual_check
    
    @staticmethod
    def normalize_identifier(code: str) -> str:
        """
        Normalize identifier by removing separators and converting to uppercase
        """
        if not code:
            return ""
        
        # Remove common separators
        normalized = re.sub(r'[-\s]', '', code.strip().upper())
        
        return normalized
    
    @staticmethod
    def format_identifier(code: str, identifier_type: str) -> str:
        """
        Format identifier for display based on type
        """
        if identifier_type == "ASIN":
            return code.upper()
        elif identifier_type in ["EAN", "UPC", "GTIN"]:
            # Format with spaces for readability
            if len(code) == 13:  # EAN-13
                return f"{code[:3]} {code[3:7]} {code[7:12]} {code[12]}"
            elif len(code) == 12:  # UPC-A
                return f"{code[0]} {code[1:6]} {code[6:11]} {code[11]}"
            elif len(code) == 8:  # EAN-8
                return f"{code[:4]} {code[4:7]} {code[7]}"
            elif len(code) == 14:  # GTIN-14
                return f"{code[:2]} {code[2:8]} {code[8:13]} {code[13]}"
        
        return code
    
    @staticmethod
    def get_identifier_info(identifier_type: str) -> dict:
        """
        Get information about an identifier type
        """
        info = {
            "ASIN": {
                "name": "Amazon Standard Identification Number",
                "description": "10-character alphanumeric code starting with 'B'",
                "example": "B0BQBXBW88",
                "length": 10
            },
            "EAN": {
                "name": "European Article Number",
                "description": "8 or 13-digit barcode standard",
                "example": "4003994155486",
                "length": [8, 13]
            },
            "UPC": {
                "name": "Universal Product Code",
                "description": "12-digit barcode standard used in North America",
                "example": "012345678905",
                "length": 12
            },
            "GTIN": {
                "name": "Global Trade Item Number",
                "description": "14-digit global standard for product identification",
                "example": "01234567890128",
                "length": 14
            }
        }
        
        return info.get(identifier_type, {
            "name": "Unknown",
            "description": "Unknown identifier type",
            "example": "",
            "length": 0
        })


def detect_and_validate_identifier(code: str) -> dict:
    """
    High-level function to detect and validate a product identifier
    
    Args:
        code: Product identifier string
        
    Returns:
        Dictionary with detection results
    """
    normalized_code = ProductIdentifier.normalize_identifier(code)
    identifier_type, is_valid = ProductIdentifier.identify_product_code(normalized_code)
    
    return {
        "original_code": code,
        "normalized_code": normalized_code,
        "identifier_type": identifier_type,
        "is_valid": is_valid,
        "formatted_code": ProductIdentifier.format_identifier(normalized_code, identifier_type),
        "info": ProductIdentifier.get_identifier_info(identifier_type),
        "can_use_for_lookup": is_valid and identifier_type in ["ASIN", "EAN", "UPC", "GTIN"]
    }
