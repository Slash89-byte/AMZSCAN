#!/usr/bin/env python3
"""
Simple Enhanced Matching Demo
Shows the enhanced matching system capabilities with test data
"""

import sys
sys.path.append('.')

from utils.enhanced_gtin_processor import EnhancedGTINProcessor

def demo_enhanced_gtin_processing():
    """Demonstrate enhanced GTIN processing capabilities"""
    print("🔍 Enhanced GTIN Processing Demo")
    print("=" * 50)
    
    processor = EnhancedGTINProcessor()
    
    # Real GTINs from various sources
    test_gtins = [
        ("3600523951369", "L'Oréal Revitalift Laser X3"),
        ("0000030080515", "L'Oréal True Match Foundation"),
        ("3607345064672", "Maybelline Concealer"),
        ("8005610636917", "Kiko Milano Lipstick"),
        ("3614273070493", "YSL Beauty Product"),
        ("123456789", "Invalid GTIN Example"),
        ("", "Missing GTIN Example")
    ]
    
    for gtin, product_name in test_gtins:
        print(f"\n📦 Product: {product_name}")
        print(f"🏷️  GTIN: '{gtin}'")
        
        result = processor.process_gtin(gtin)
        
        # Show validation results
        if result['is_valid']:
            print(f"✅ Valid: {result['confidence']}% confidence")
            print(f"📋 Format: {result['format']}")
            print(f"🔧 Normalized: {result['normalized']}")
            print(f"🔍 Search Variants: {result['search_variants']}")
            
            # Show confidence level
            confidence = result['confidence']
            if confidence >= 90:
                level = "🟢 HIGH"
            elif confidence >= 70:
                level = "🟡 MEDIUM"
            elif confidence > 0:
                level = "🔴 LOW"
            else:
                level = "⚫ NONE"
            print(f"📊 Confidence Level: {level}")
        else:
            print(f"❌ Invalid: {result['confidence']}% confidence")
            if result['confidence'] > 0:
                print(f"⚠️  Partial validation possible")
    
    print("\n" + "=" * 50)
    print("✨ Enhanced GTIN processing provides:")
    print("  • Comprehensive validation for all GTIN formats")
    print("  • Confidence scoring (0-100%)")
    print("  • Multiple search variants for better Amazon matching")
    print("  • Graceful handling of invalid/missing GTINs")

def demo_matching_strategy():
    """Demonstrate the multi-strategy matching approach"""
    print("\n\n🎯 Multi-Strategy Matching Demo")
    print("=" * 50)
    
    print("📋 Matching Strategy Order:")
    print("1. 🏷️  Primary GTIN Lookup")
    print("   • Validate and normalize GTIN")
    print("   • Try multiple GTIN variants")
    print("   • High confidence (90-95%)")
    
    print("\n2. 🔄 GTIN Variant Search")
    print("   • Try different GTIN formats")
    print("   • Add/remove leading zeros")
    print("   • Medium-high confidence (70-90%)")
    
    print("\n3. 🔍 Brand + Name Fallback")
    print("   • Clean product name (remove ml, g, etc.)")
    print("   • Search: 'Brand + Cleaned Name'")
    print("   • Search: 'Brand + Original Name'")
    print("   • Medium confidence (60%)")
    
    print("\n4. 📝 Name-Only Search")
    print("   • Search cleaned product name")
    print("   • Search original product name")
    print("   • Lower confidence (40-60%)")
    
    print("\n🎨 Visual Indicators:")
    print("  🟢 Green: High confidence matches (90%+)")
    print("  🟡 Yellow: Medium confidence matches (70-89%)")
    print("  🔵 Blue: Brand+name fallback matches (60%)")
    print("  🔴 Red: Low confidence or failed matches")

def demo_business_benefits():
    """Show business benefits of enhanced matching"""
    print("\n\n💼 Business Benefits")
    print("=" * 50)
    
    print("📈 Improved Accuracy:")
    print("  • Before: Basic GTIN lookup only")
    print("  • After: 95% GTIN validation + smart fallbacks")
    print("  • Result: Higher match success rate")
    
    print("\n⚡ Better Coverage:")
    print("  • Handles invalid/missing GTINs")
    print("  • Multiple search strategies")
    print("  • Fallback to brand + name search")
    
    print("\n🎯 Informed Decisions:")
    print("  • Confidence scoring shows match quality")
    print("  • Color-coded visual feedback")
    print("  • Users know which matches to trust")
    
    print("\n🔧 Production Ready:")
    print("  • Rate limiting for API protection")
    print("  • Graceful error handling")
    print("  • Comprehensive logging")
    print("  • Scalable for large catalogs")

def main():
    """Run the demo"""
    print("🚀 Enhanced Product Matching System Demo")
    print("=" * 60)
    
    demo_enhanced_gtin_processing()
    demo_matching_strategy()
    demo_business_benefits()
    
    print("\n\n✅ Demo Complete!")
    print("💡 The enhanced system is ready for production testing")
    print("🔧 Configure your Keepa API for live Amazon matching")

if __name__ == "__main__":
    main()
