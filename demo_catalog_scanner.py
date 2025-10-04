"""
Demo script for Catalog Scanner module

Tests the complete workflow:
1. Create sample catalog file
2. Parse and detect columns
3. Review suggested mappings
4. Display statistics
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.catalog_parser import CatalogParser, create_sample_catalog
from utils.column_detector import ColumnDetector
from utils.template_manager import TemplateManager


def print_section(title: str):
    """Print formatted section header"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}\n")


def demo_parser():
    """Demonstrate catalog parsing"""
    print_section("1. CATALOG PARSER DEMO")
    
    # Create sample catalog
    sample_file = "demo_catalog.csv"
    print(f"📁 Creating sample catalog: {sample_file}")
    create_sample_catalog(sample_file, 'csv')
    print(f"✅ Sample catalog created")
    
    # Parse the catalog
    parser = CatalogParser()
    print(f"\n🔍 Parsing catalog file...")
    catalog_data = parser.parse_file(sample_file)
    
    print(f"✅ Parsing successful!")
    print(f"\n📊 Catalog Information:")
    print(f"   - File format: {catalog_data.file_format}")
    print(f"   - Encoding: {catalog_data.encoding}")
    print(f"   - Header row: {catalog_data.header_row_index}")
    print(f"   - Total rows: {catalog_data.total_rows}")
    print(f"   - Columns: {len(catalog_data.headers)}")
    print(f"   - Detected currency: {catalog_data.detected_currency or 'None'}")
    
    print(f"\n📋 Column Headers:")
    for i, header in enumerate(catalog_data.headers, 1):
        print(f"   {i}. {header}")
    
    print(f"\n📦 Sample Data (first 2 rows):")
    for i, row in enumerate(catalog_data.rows[:2], 1):
        print(f"\n   Row {i}:")
        for header, value in row.items():
            if value:  # Only show non-empty values
                print(f"      {header}: {value}")
    
    # Validate
    print(f"\n✅ Validating data...")
    validation = parser.validate_data(catalog_data)
    print(f"   Valid: {validation['is_valid']}")
    print(f"   Empty rows: {validation['stats']['empty_rows']}")
    print(f"   Complete rows: {validation['stats']['complete_rows']}")
    
    if validation['warnings']:
        print(f"\n⚠️  Warnings:")
        for warning in validation['warnings']:
            print(f"   - {warning}")
    
    return catalog_data


def demo_column_detector(catalog_data):
    """Demonstrate column detection"""
    print_section("2. COLUMN DETECTOR DEMO")
    
    detector = ColumnDetector(min_confidence=0.6)
    
    print(f"🔍 Detecting column purposes...")
    detection_result = detector.detect_columns(
        catalog_data.headers,
        catalog_data.rows[:20]
    )
    
    print(f"✅ Detection complete!")
    print(f"\n📊 Detection Results:")
    print(f"   - Mappings found: {len(detection_result.mappings)}")
    print(f"   - Overall confidence: {detection_result.confidence_score:.1%}")
    print(f"   - Unmapped columns: {len(detection_result.unmapped_columns)}")
    
    print(f"\n🗺️  Column Mappings:")
    for mapping in detection_result.mappings:
        confidence_emoji = "🟢" if mapping.confidence >= 0.8 else "🟡" if mapping.confidence >= 0.6 else "🔴"
        print(f"   {confidence_emoji} {mapping.catalog_column:25s} → {mapping.standard_field:20s} "
              f"({mapping.confidence:.0%}, {mapping.detection_method})")
    
    if detection_result.unmapped_columns:
        print(f"\n❓ Unmapped Columns:")
        for col in detection_result.unmapped_columns:
            print(f"   - {col}")
            # Get suggestions
            suggestions = detector.suggest_mapping(col, ['gtin', 'product_name', 'brand', 'wholesale_price', 'stock'])
            if suggestions:
                print(f"      Suggestions: {', '.join([f'{field} ({conf:.0%})' for field, conf in suggestions[:2]])}")
    
    if detection_result.warnings:
        print(f"\n⚠️  Warnings:")
        for warning in detection_result.warnings:
            print(f"   - {warning}")
    
    return detection_result


def demo_template_manager(detection_result):
    """Demonstrate template management"""
    print_section("3. TEMPLATE MANAGER DEMO")
    
    manager = TemplateManager()
    
    # Create column mappings from detection
    column_mappings = {m.catalog_column: m.standard_field 
                      for m in detection_result.mappings}
    
    # Save template
    print(f"💾 Saving template...")
    wholesaler_name = "Demo Wholesaler"
    success = manager.save_template(
        name=wholesaler_name,
        column_mappings=column_mappings,
        currency='EUR',
        vat_included=True,
        metadata={
            'file_format': 'csv',
            'delimiter': ',',
            'note': 'Sample catalog for testing'
        }
    )
    
    if success:
        print(f"✅ Template saved: {wholesaler_name}")
    
    # List templates
    print(f"\n📋 Available Templates:")
    templates = manager.list_templates()
    for i, template in enumerate(templates, 1):
        print(f"   {i}. {template['name']}")
        print(f"      - Currency: {template['currency']}")
        print(f"      - VAT included: {template['vat_included']}")
        print(f"      - Columns: {template['column_count']}")
        print(f"      - Used: {template['use_count']} times")
        print(f"      - Last used: {template['last_used_date'][:10]}")
    
    # Test template matching
    print(f"\n🔍 Testing template matching...")
    test_headers = ["EAN", "Product Name", "Brand", "Wholesale Price €"]
    matched = manager.find_matching_template(test_headers, "demo_catalog.csv")
    if matched:
        print(f"✅ Found matching template: {matched}")
    else:
        print(f"❌ No matching template found")
    
    # Test template suggestions
    print(f"\n💡 Template suggestions for current file:")
    suggestions = manager.suggest_templates(test_headers, top_n=3)
    for name, confidence in suggestions:
        print(f"   - {name}: {confidence:.0%} match")


def demo_statistics(catalog_data, detection_result):
    """Display final statistics"""
    print_section("4. SUMMARY STATISTICS")
    
    # Count mappings by type
    mapped_by_type = {}
    for mapping in detection_result.mappings:
        field_type = mapping.standard_field.split('_')[0]  # e.g., 'wholesale' from 'wholesale_price'
        mapped_by_type[field_type] = mapped_by_type.get(field_type, 0) + 1
    
    print(f"📊 Analysis Summary:")
    print(f"   - Total products: {catalog_data.total_rows}")
    print(f"   - Total columns: {len(catalog_data.headers)}")
    print(f"   - Mapped columns: {len(detection_result.mappings)}")
    print(f"   - Unmapped columns: {len(detection_result.unmapped_columns)}")
    print(f"   - Overall confidence: {detection_result.confidence_score:.1%}")
    
    print(f"\n🎯 Readiness Check:")
    critical_fields = ['gtin', 'wholesale_price', 'product_name']
    mapped_fields = {m.standard_field for m in detection_result.mappings}
    
    for field in critical_fields:
        status = "✅" if field in mapped_fields else "❌"
        print(f"   {status} {field}")
    
    has_all_critical = all(field in mapped_fields for field in critical_fields)
    
    if has_all_critical:
        print(f"\n🚀 Ready for scanning!")
        print(f"   All critical fields detected. You can proceed with Amazon matching.")
    else:
        missing = [f for f in critical_fields if f not in mapped_fields]
        print(f"\n⚠️  Manual mapping required!")
        print(f"   Missing critical fields: {', '.join(missing)}")
        print(f"   Please review and adjust mappings before scanning.")
    
    print(f"\n💡 Next Steps:")
    print(f"   1. Review column mappings in the GUI")
    print(f"   2. Adjust currency and VAT settings")
    print(f"   3. Start catalog scan")
    print(f"   4. Export profitable products")


def main():
    """Run the complete demo"""
    print("\n" + "="*60)
    print(" 📦 CATALOG SCANNER DEMO")
    print(" Testing smart catalog parsing and column detection")
    print("="*60)
    
    try:
        # Demo each component
        catalog_data = demo_parser()
        detection_result = demo_column_detector(catalog_data)
        demo_template_manager(detection_result)
        demo_statistics(catalog_data, detection_result)
        
        print_section("✅ DEMO COMPLETED SUCCESSFULLY")
        print("All components working correctly!")
        print("\nTo use the Catalog Scanner:")
        print("  1. Run: python main.py")
        print("  2. Select '📦 Catalog Scanner'")
        print("  3. Upload your wholesaler catalog")
        print("  4. Review and adjust mappings")
        print("  5. Start scanning!")
        
        # Cleanup
        sample_file = "demo_catalog.csv"
        if os.path.exists(sample_file):
            os.remove(sample_file)
            print(f"\n🧹 Cleaned up demo file: {sample_file}")
        
    except Exception as e:
        print(f"\n❌ Error during demo: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
