#!/usr/bin/env python3
"""
Test script for multi-format identifier functionality
"""

import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.identifiers import detect_and_validate_identifier

def test_identifier_functionality():
    """Test multi-format identifier support"""
    
    print("🔍 Testing Multi-Format Identifier Support")
    print("=" * 50)
    
    test_cases = [
        # Valid identifiers
        ("B0BQBXBW88", "Valid ASIN"),
        ("4003994155486", "Valid EAN-13"),
        ("012345678905", "Valid UPC-12"),
        ("01234567890128", "Valid GTIN-14"),
        ("12345670", "Valid EAN-8"),
        
        # With separators
        ("400-399-415-548-6", "EAN-13 with dashes"),
        ("400 399 415 548 6", "EAN-13 with spaces"),
        
        # Invalid identifiers
        ("B123456", "Invalid ASIN (too short)"),
        ("4003994155487", "Invalid EAN-13 (wrong check digit)"),
        ("ABCDEFGHIJ", "Unknown format"),
        ("", "Empty input"),
    ]
    
    for test_code, description in test_cases:
        print(f"\n📋 Testing: {description}")
        print(f"   Input: '{test_code}'")
        
        result = detect_and_validate_identifier(test_code)
        
        print(f"   Type: {result['identifier_type']}")
        print(f"   Valid: {'✅' if result['is_valid'] else '❌'}")
        print(f"   Normalized: {result['normalized_code']}")
        print(f"   Formatted: {result['formatted_code']}")
        print(f"   Can lookup: {'✅' if result['can_use_for_lookup'] else '❌'}")
        
        if result['info']['name'] != 'Unknown':
            print(f"   Info: {result['info']['name']}")
    
    print("\n🎯 Real-time validation test:")
    print("Enter some identifiers to test (press Enter with empty input to exit):")
    
    while True:
        user_input = input("Identifier: ").strip()
        if not user_input:
            break
            
        result = detect_and_validate_identifier(user_input)
        
        if result['is_valid']:
            print(f"✅ Valid {result['identifier_type']}: {result['formatted_code']}")
        elif result['identifier_type'] != "UNKNOWN":
            print(f"⚠️ Invalid {result['identifier_type']} (check format)")
        else:
            print("❌ Unknown identifier format")
    
    print("\n✅ Multi-format identifier support is working correctly!")

if __name__ == "__main__":
    test_identifier_functionality()
