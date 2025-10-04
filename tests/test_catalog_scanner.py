"""
Unit tests for Catalog Scanner components

Tests:
- CatalogParser: File parsing, header detection, validation
- ColumnDetector: Column mapping, pattern recognition
- TemplateManager: Template save/load, matching
"""

import pytest
import os
import tempfile
import json
from pathlib import Path

from utils.catalog_parser import CatalogParser, create_sample_catalog, CatalogData
from utils.column_detector import ColumnDetector, ColumnMapping, DetectionResult
from utils.template_manager import TemplateManager, WholesalerTemplate


class TestCatalogParser:
    """Test CatalogParser functionality"""
    
    def setup_method(self):
        """Setup for each test"""
        self.parser = CatalogParser()
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Cleanup after each test"""
        # Clean up temp files
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_create_sample_catalog(self):
        """Test sample catalog creation"""
        filepath = os.path.join(self.temp_dir, 'test_sample.csv')
        create_sample_catalog(filepath, 'csv')
        
        assert os.path.exists(filepath)
        
        # Verify content
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            assert 'EAN' in content
            assert 'Product Name' in content
            assert 'Wholesale Price' in content
    
    def test_parse_csv_with_metadata_rows(self):
        """Test parsing CSV with metadata rows before headers"""
        filepath = os.path.join(self.temp_dir, 'test_metadata.csv')
        create_sample_catalog(filepath, 'csv')
        
        catalog_data = self.parser.parse_file(filepath)
        
        assert isinstance(catalog_data, CatalogData)
        assert catalog_data.file_format == 'csv'
        assert catalog_data.header_row_index == 3  # Headers on row 4 (0-indexed)
        assert catalog_data.total_rows == 4
        assert len(catalog_data.headers) == 7
        assert 'EAN' in catalog_data.headers
    
    def test_parse_real_wholesaler_catalog(self):
        """Test parsing the actual wholesaler catalog"""
        catalog_path = 'assets/Catalog_for_Seller_RD997Z-7Z9O6.xlsx'
        
        if not os.path.exists(catalog_path):
            pytest.skip("Wholesaler catalog not found")
        
        catalog_data = self.parser.parse_file(catalog_path, max_rows=100)
        
        assert isinstance(catalog_data, CatalogData)
        assert catalog_data.file_format == 'excel'
        assert catalog_data.header_row_index >= 0
        assert catalog_data.total_rows > 0
        assert len(catalog_data.headers) > 0
        
        # Check expected columns from Qogita catalog
        headers_lower = [h.lower() for h in catalog_data.headers]
        assert any('gtin' in h for h in headers_lower)
        assert any('name' in h or 'product' in h for h in headers_lower)
        assert any('price' in h for h in headers_lower)
    
    def test_detect_delimiter(self):
        """Test CSV delimiter detection"""
        # Test comma delimiter
        sample = "col1,col2,col3\nval1,val2,val3\n"
        delimiter = self.parser._detect_delimiter(sample)
        assert delimiter == ','
        
        # Test semicolon delimiter
        sample = "col1;col2;col3\nval1;val2;val3\n"
        delimiter = self.parser._detect_delimiter(sample)
        assert delimiter == ';'
    
    def test_find_header_row(self):
        """Test header row detection"""
        rows = [
            ['Title Row'],
            ['Metadata: 2025-10-04'],
            [],
            ['GTIN', 'Name', 'Price', 'Stock'],
            ['123456789', 'Product 1', '10.50', '100']
        ]
        
        index, headers = self.parser._find_header_row(rows)
        
        assert index == 3
        assert headers == ['GTIN', 'Name', 'Price', 'Stock']
    
    def test_score_header_row(self):
        """Test header row scoring"""
        # Good header row
        header_row = ['GTIN', 'Product Name', 'Wholesale Price', 'Stock']
        score = self.parser._score_header_row(header_row)
        assert score > 5  # Should have high score
        
        # Data row (should have low score)
        data_row = ['123456789', 'Some Product', '10.50', '100']
        score = self.parser._score_header_row(data_row)
        assert score < 5  # Should have low score
    
    def test_detect_currency(self):
        """Test currency detection"""
        headers = ['Name', 'Price EUR', 'Stock']
        rows = [
            {'Name': 'Product 1', 'Price EUR': '€10.50', 'Stock': '100'},
            {'Name': 'Product 2', 'Price EUR': '€15.00', 'Stock': '50'}
        ]
        
        currency = self.parser._detect_currency(rows, headers)
        assert currency == 'EUR'
    
    def test_validate_data(self):
        """Test data validation"""
        filepath = os.path.join(self.temp_dir, 'test_validate.csv')
        create_sample_catalog(filepath, 'csv')
        
        catalog_data = self.parser.parse_file(filepath)
        validation = self.parser.validate_data(catalog_data)
        
        assert validation['is_valid'] is True
        assert 'errors' in validation
        assert 'warnings' in validation
        assert 'stats' in validation


class TestColumnDetector:
    """Test ColumnDetector functionality"""
    
    def setup_method(self):
        """Setup for each test"""
        self.detector = ColumnDetector(min_confidence=0.6)
    
    def test_detect_exact_matches(self):
        """Test exact column name matching"""
        headers = ['GTIN', 'Product Name', 'Brand', 'Category', 'Price']
        sample_rows = []
        
        result = self.detector.detect_columns(headers, sample_rows)
        
        assert isinstance(result, DetectionResult)
        assert len(result.mappings) >= 4  # Should map at least 4 columns
        
        # Check specific mappings
        mapped_fields = {m.standard_field for m in result.mappings}
        assert 'gtin' in mapped_fields
        assert 'product_name' in mapped_fields
        assert 'brand' in mapped_fields
    
    def test_detect_fuzzy_matches(self):
        """Test fuzzy column name matching"""
        headers = ['EAN', 'Item Name', 'Manufacturer', 'Wholesale Price €']
        sample_rows = []
        
        result = self.detector.detect_columns(headers, sample_rows)
        
        # Check fuzzy matches
        mappings_dict = {m.catalog_column: m.standard_field for m in result.mappings}
        
        # EAN should map to gtin
        assert 'EAN' in mappings_dict
        assert mappings_dict['EAN'] == 'gtin'
        
        # Item Name should map to product_name
        assert 'Item Name' in mappings_dict
        assert mappings_dict['Item Name'] == 'product_name'
    
    def test_detect_with_real_wholesaler_data(self):
        """Test detection on real wholesaler catalog"""
        catalog_path = 'assets/Catalog_for_Seller_RD997Z-7Z9O6.xlsx'
        
        if not os.path.exists(catalog_path):
            pytest.skip("Wholesaler catalog not found")
        
        parser = CatalogParser()
        catalog_data = parser.parse_file(catalog_path, max_rows=50)
        
        result = self.detector.detect_columns(
            catalog_data.headers,
            catalog_data.rows[:20]
        )
        
        assert len(result.mappings) > 0
        assert result.confidence_score > 0.5
        
        # Should detect critical fields
        mapped_fields = {m.standard_field for m in result.mappings}
        assert 'gtin' in mapped_fields or 'sku' in mapped_fields
        assert 'product_name' in mapped_fields
        assert 'wholesale_price' in mapped_fields or 'retail_price' in mapped_fields
    
    def test_pattern_matching(self):
        """Test pattern-based column detection"""
        headers = ['ProductCode', 'Description', 'Cost']
        sample_rows = [
            {'ProductCode': '3614227991341', 'Description': 'Product Name', 'Cost': '10.50'},
            {'ProductCode': '3600523351534', 'Description': 'Another Product', 'Cost': '15.00'},
            {'ProductCode': '8411061976111', 'Description': 'Third Product', 'Cost': '8.99'}
        ]
        
        result = self.detector.detect_columns(headers, sample_rows)
        
        mappings_dict = {m.catalog_column: m.standard_field for m in result.mappings}
        
        # ProductCode should be detected as GTIN by pattern (13-digit codes)
        assert 'ProductCode' in mappings_dict
        # Could be gtin or sku based on pattern
        assert mappings_dict['ProductCode'] in ['gtin', 'sku']
    
    def test_string_similarity(self):
        """Test string similarity calculation"""
        # Exact match or substring match
        similarity = self.detector._string_similarity('price', 'price')
        assert similarity >= 0.9  # High similarity for exact/substring
        
        # High similarity
        similarity = self.detector._string_similarity('wholesale price', 'price')
        assert similarity > 0.5
        
        # Low similarity
        similarity = self.detector._string_similarity('price', 'stock')
        assert similarity < 0.5
    
    def test_suggest_mapping(self):
        """Test mapping suggestions for unmapped columns"""
        unmapped = 'Item Code'
        available = ['gtin', 'sku', 'product_name', 'brand']
        
        suggestions = self.detector.suggest_mapping(unmapped, available)
        
        assert len(suggestions) > 0
        assert all(isinstance(s, tuple) for s in suggestions)
        assert all(len(s) == 2 for s in suggestions)  # (field, confidence)
        
        # SKU should be suggested
        suggested_fields = [s[0] for s in suggestions]
        assert 'sku' in suggested_fields


class TestTemplateManager:
    """Test TemplateManager functionality"""
    
    def setup_method(self):
        """Setup for each test"""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = TemplateManager(templates_dir=self.temp_dir)
    
    def teardown_method(self):
        """Cleanup after each test"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_save_template(self):
        """Test saving a template"""
        mappings = {
            'GTIN': 'gtin',
            'Product Name': 'product_name',
            'Price': 'wholesale_price'
        }
        
        success = self.manager.save_template(
            name='Test Wholesaler',
            column_mappings=mappings,
            currency='EUR',
            vat_included=True,
            metadata={'test': 'data'}
        )
        
        assert success is True
        assert 'Test Wholesaler' in self.manager.templates
        
        template = self.manager.templates['Test Wholesaler']
        assert template.name == 'Test Wholesaler'
        assert template.currency == 'EUR'
        assert template.vat_included is True
        assert template.use_count == 1
    
    def test_get_template(self):
        """Test retrieving a template"""
        mappings = {'GTIN': 'gtin', 'Name': 'product_name'}
        self.manager.save_template('Test', mappings, 'EUR', False)
        
        template = self.manager.get_template('Test')
        
        assert template is not None
        assert template.name == 'Test'
        assert template.use_count == 2  # Incremented on get
    
    def test_list_templates(self):
        """Test listing all templates"""
        self.manager.save_template('Wholesaler A', {'GTIN': 'gtin'}, 'EUR', True)
        self.manager.save_template('Wholesaler B', {'EAN': 'gtin'}, 'USD', False)
        
        templates = self.manager.list_templates()
        
        assert len(templates) == 2
        assert all('name' in t for t in templates)
        assert all('currency' in t for t in templates)
        assert all('use_count' in t for t in templates)
    
    def test_delete_template(self):
        """Test deleting a template"""
        self.manager.save_template('To Delete', {'GTIN': 'gtin'}, 'EUR', True)
        
        success = self.manager.delete_template('To Delete')
        
        assert success is True
        assert 'To Delete' not in self.manager.templates
    
    def test_find_matching_template(self):
        """Test finding matching template"""
        mappings = {'GTIN': 'gtin', 'Product Name': 'product_name', 'Price': 'wholesale_price'}
        self.manager.save_template('Test Wholesaler', mappings, 'EUR', True)
        
        # Test with matching headers
        headers = ['GTIN', 'Product Name', 'Price', 'Stock']
        matched = self.manager.find_matching_template(headers, 'test_wholesaler_oct.csv')
        
        # Should find match based on column overlap and filename
        assert matched == 'Test Wholesaler'
    
    def test_suggest_templates(self):
        """Test template suggestions"""
        self.manager.save_template('Wholesaler A', {'GTIN': 'gtin', 'Name': 'product_name'}, 'EUR', True)
        self.manager.save_template('Wholesaler B', {'EAN': 'gtin', 'Price': 'wholesale_price'}, 'USD', False)
        
        headers = ['GTIN', 'Name', 'Category']
        suggestions = self.manager.suggest_templates(headers, top_n=2)
        
        assert len(suggestions) > 0
        assert all(isinstance(s, tuple) for s in suggestions)
        
        # Wholesaler A should be suggested (more overlap)
        suggested_names = [s[0] for s in suggestions]
        assert 'Wholesaler A' in suggested_names
    
    def test_export_import_template(self):
        """Test exporting and importing templates"""
        mappings = {'GTIN': 'gtin', 'Name': 'product_name'}
        self.manager.save_template('Export Test', mappings, 'EUR', True)
        
        # Export
        export_path = os.path.join(self.temp_dir, 'exported_template.json')
        success = self.manager.export_template('Export Test', export_path)
        assert success is True
        assert os.path.exists(export_path)
        
        # Create new manager
        new_temp_dir = tempfile.mkdtemp()
        new_manager = TemplateManager(templates_dir=new_temp_dir)
        
        # Import
        imported_name = new_manager.import_template(export_path)
        assert imported_name == 'Export Test'
        assert 'Export Test' in new_manager.templates
        
        # Cleanup
        import shutil
        shutil.rmtree(new_temp_dir)
    
    def test_template_persistence(self):
        """Test that templates persist across manager instances"""
        mappings = {'GTIN': 'gtin'}
        self.manager.save_template('Persistent', mappings, 'EUR', True)
        
        # Create new manager with same directory
        new_manager = TemplateManager(templates_dir=self.temp_dir)
        
        assert 'Persistent' in new_manager.templates
        template = new_manager.get_template('Persistent')
        assert template.name == 'Persistent'


class TestIntegration:
    """Integration tests for complete workflows"""
    
    def test_complete_parsing_and_detection_workflow(self):
        """Test complete workflow: parse → detect → validate"""
        # Create sample catalog
        temp_dir = tempfile.mkdtemp()
        filepath = os.path.join(temp_dir, 'test_catalog.csv')
        create_sample_catalog(filepath, 'csv')
        
        try:
            # Parse
            parser = CatalogParser()
            catalog_data = parser.parse_file(filepath)
            
            assert catalog_data.total_rows > 0
            
            # Detect columns
            detector = ColumnDetector()
            detection_result = detector.detect_columns(
                catalog_data.headers,
                catalog_data.rows[:10]
            )
            
            assert len(detection_result.mappings) > 0
            assert detection_result.confidence_score > 0.5
            
            # Validate
            validation = parser.validate_data(catalog_data)
            assert validation['is_valid'] is True
            
        finally:
            import shutil
            shutil.rmtree(temp_dir)
    
    def test_template_workflow_with_real_catalog(self):
        """Test complete template workflow with real wholesaler catalog"""
        catalog_path = 'assets/Catalog_for_Seller_RD997Z-7Z9O6.xlsx'
        
        if not os.path.exists(catalog_path):
            pytest.skip("Wholesaler catalog not found")
        
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Parse catalog
            parser = CatalogParser()
            catalog_data = parser.parse_file(catalog_path, max_rows=50)
            
            # Detect columns
            detector = ColumnDetector()
            detection_result = detector.detect_columns(
                catalog_data.headers,
                catalog_data.rows[:20]
            )
            
            # Create template
            manager = TemplateManager(templates_dir=temp_dir)
            mappings = {m.catalog_column: m.standard_field for m in detection_result.mappings}
            
            success = manager.save_template(
                name='RD997Z Wholesaler',
                column_mappings=mappings,
                currency=catalog_data.detected_currency or 'EUR',
                vat_included=False
            )
            
            assert success is True
            
            # Test template matching
            matched = manager.find_matching_template(
                catalog_data.headers,
                'Catalog_for_Seller_RD997Z-7Z9O6.xlsx'
            )
            
            assert matched is not None
            
        finally:
            import shutil
            shutil.rmtree(temp_dir)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
