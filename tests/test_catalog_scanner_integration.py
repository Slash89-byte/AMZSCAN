"""
Integration tests for Catalog Scanner GUI module

Tests the complete GUI workflow including:
- File upload and parsing
- Column mapping review
- Template management
- Scan worker functionality
"""

import pytest
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
import sys

# Ensure QApplication exists
if not QApplication.instance():
    app = QApplication(sys.argv)

from gui.catalog_scanner import CatalogScannerWindow, ColumnMappingDialog, CatalogScanWorker
from utils.catalog_parser import CatalogParser, create_sample_catalog
from utils.column_detector import ColumnDetector, DetectionResult, ColumnMapping
from utils.product_matcher import QogitaProduct, MatchedProduct


class TestCatalogScannerWindow:
    """Test CatalogScannerWindow GUI"""
    
    def setup_method(self):
        """Setup for each test"""
        self.window = CatalogScannerWindow()
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Cleanup after each test"""
        self.window.close()
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_window_initialization(self):
        """Test window initializes correctly"""
        assert self.window is not None
        assert self.window.catalog_parser is not None
        assert self.window.column_detector is not None
        assert self.window.template_manager is not None
        assert self.window.product_matcher is not None
    
    def test_ui_components_exist(self):
        """Test all UI components are created"""
        assert self.window.file_label is not None
        assert self.window.wholesaler_input is not None
        assert self.window.currency_combo is not None
        assert self.window.vat_checkbox is not None
        assert self.window.vat_rate_spin is not None
        assert self.window.review_mapping_btn is not None
        assert self.window.load_template_btn is not None
        assert self.window.save_template_btn is not None
        assert self.window.scan_btn is not None
        assert self.window.stop_btn is not None
        assert self.window.export_btn is not None
        assert self.window.progress_bar is not None
        assert self.window.log_text is not None
        assert self.window.results_table is not None
    
    def test_initial_button_states(self):
        """Test initial button enabled/disabled states"""
        assert self.window.review_mapping_btn.isEnabled() is False
        assert self.window.save_template_btn.isEnabled() is False
        assert self.window.scan_btn.isEnabled() is False
        assert self.window.stop_btn.isEnabled() is False
        assert self.window.export_btn.isEnabled() is False
    
    def test_upload_file_enables_buttons(self):
        """Test that uploading file enables appropriate buttons"""
        # Create sample catalog
        filepath = os.path.join(self.temp_dir, 'test.csv')
        create_sample_catalog(filepath, 'csv')
        
        # Simulate file upload
        with patch('PyQt6.QtWidgets.QFileDialog.getOpenFileName', return_value=(filepath, '')):
            self.window.upload_file()
        
        # Check states
        assert self.window.catalog_data is not None
        assert self.window.review_mapping_btn.isEnabled() is True
        assert self.window.save_template_btn.isEnabled() is True
        assert self.window.scan_btn.isEnabled() is True
    
    def test_detect_columns_creates_mappings(self):
        """Test column detection creates mappings"""
        # Create and parse sample catalog
        filepath = os.path.join(self.temp_dir, 'test.csv')
        create_sample_catalog(filepath, 'csv')
        
        parser = CatalogParser()
        self.window.catalog_data = parser.parse_file(filepath)
        
        # Detect columns
        self.window.detect_columns('test.csv')
        
        assert len(self.window.column_mappings) > 0
        assert 'gtin' in self.window.column_mappings.values()
    
    def test_add_log_message(self):
        """Test adding log messages"""
        initial_text = self.window.log_text.toPlainText()
        
        self.window.add_log("Test message")
        
        final_text = self.window.log_text.toPlainText()
        assert final_text != initial_text
        assert "Test message" in final_text
    
    def test_vat_checkbox_enables_rate_spin(self):
        """Test VAT checkbox enables/disables rate spinner"""
        assert self.window.vat_rate_spin.isEnabled() is False
        
        self.window.vat_checkbox.setChecked(True)
        assert self.window.vat_rate_spin.isEnabled() is True
        
        self.window.vat_checkbox.setChecked(False)
        assert self.window.vat_rate_spin.isEnabled() is False


class TestColumnMappingDialog:
    """Test ColumnMappingDialog"""
    
    def setup_method(self):
        """Setup for each test"""
        # Create mock detection result
        mappings = [
            ColumnMapping('GTIN', 'gtin', 1.0, 'exact'),
            ColumnMapping('Product Name', 'product_name', 0.95, 'fuzzy'),
            ColumnMapping('Price', 'wholesale_price', 0.85, 'fuzzy')
        ]
        
        self.detection_result = DetectionResult(
            mappings=mappings,
            unmapped_columns=['Unknown Column'],
            confidence_score=0.93,
            warnings=['Warning message']
        )
        
        self.catalog_headers = ['GTIN', 'Product Name', 'Price', 'Unknown Column']
        self.dialog = ColumnMappingDialog(self.detection_result, self.catalog_headers)
    
    def teardown_method(self):
        """Cleanup"""
        self.dialog.close()
    
    def test_dialog_initialization(self):
        """Test dialog initializes with correct data"""
        assert self.dialog is not None
        assert self.dialog.mapping_table is not None
        assert self.dialog.mapping_table.rowCount() == 3  # 3 mappings
    
    def test_get_mappings(self):
        """Test getting final mappings"""
        mappings = self.dialog.get_mappings()
        
        assert isinstance(mappings, dict)
        assert 'GTIN' in mappings
        assert mappings['GTIN'] == 'gtin'


class TestCatalogScanWorker:
    """Test CatalogScanWorker thread"""
    
    def setup_method(self):
        """Setup for each test"""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create sample catalog
        filepath = os.path.join(self.temp_dir, 'test.csv')
        create_sample_catalog(filepath, 'csv')
        
        parser = CatalogParser()
        self.catalog_data = parser.parse_file(filepath)
        
        self.column_mappings = {
            'EAN': 'gtin',
            'Product Name': 'product_name',
            'Brand': 'brand',
            'Category': 'category',
            'Wholesale Price €': 'wholesale_price',
            'Stock': 'stock'
        }
        
        # Mock product matcher
        self.mock_matcher = Mock()
    
    def teardown_method(self):
        """Cleanup"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_worker_initialization(self):
        """Test worker initializes correctly"""
        worker = CatalogScanWorker(
            self.catalog_data,
            self.column_mappings,
            'EUR',
            False,
            20.0,
            self.mock_matcher
        )
        
        assert worker is not None
        assert worker.catalog_data == self.catalog_data
        assert worker.column_mappings == self.column_mappings
        assert worker.currency == 'EUR'
        assert worker.vat_included is False
        assert worker.vat_rate == 20.0
    
    def test_create_qogita_product(self):
        """Test creating QogitaProduct from row data"""
        worker = CatalogScanWorker(
            self.catalog_data,
            self.column_mappings,
            'EUR',
            False,
            20.0,
            self.mock_matcher
        )
        
        row_data = self.catalog_data.rows[0]
        product = worker._create_qogita_product(row_data)
        
        assert product is not None
        assert isinstance(product, QogitaProduct)
        assert len(product.gtin) > 0
        assert len(product.name) > 0
        assert product.wholesale_price > 0
    
    def test_parse_price(self):
        """Test price parsing"""
        worker = CatalogScanWorker(
            self.catalog_data,
            self.column_mappings,
            'EUR',
            False,
            20.0,
            self.mock_matcher
        )
        
        # Test various price formats
        assert worker._parse_price('€10.50') == 10.50
        assert worker._parse_price('$15.99') == 15.99
        assert worker._parse_price('10,50') == 10.50
        assert worker._parse_price('1 234.56') == 1234.56
    
    def test_vat_calculation(self):
        """Test VAT is correctly removed from prices"""
        worker = CatalogScanWorker(
            self.catalog_data,
            self.column_mappings,
            'EUR',
            True,  # VAT included
            20.0,
            self.mock_matcher
        )
        
        # Price with VAT: €12.00
        # Net price should be: €12.00 / 1.20 = €10.00
        row_data = self.catalog_data.rows[0].copy()
        row_data['Wholesale Price €'] = '€12.00'
        
        product = worker._create_qogita_product(row_data)
        
        assert product is not None
        # Allow for floating point precision
        assert abs(product.wholesale_price - 10.0) < 0.01


class TestRealCatalogIntegration:
    """Integration tests with real wholesaler catalog"""
    
    def test_parse_real_catalog(self):
        """Test parsing real wholesaler catalog"""
        catalog_path = 'assets/Catalog_for_Seller_RD997Z-7Z9O6.xlsx'
        
        if not os.path.exists(catalog_path):
            pytest.skip("Wholesaler catalog not found")
        
        parser = CatalogParser()
        catalog_data = parser.parse_file(catalog_path, max_rows=100)
        
        # Validate structure
        assert catalog_data is not None
        assert catalog_data.total_rows > 0
        assert len(catalog_data.headers) >= 7
        
        # Check for expected columns
        headers_lower = [h.lower() for h in catalog_data.headers]
        assert any('gtin' in h for h in headers_lower)
        assert any('name' in h for h in headers_lower)
        assert any('price' in h for h in headers_lower)
        
        # Validate first row has data
        if catalog_data.rows:
            first_row = catalog_data.rows[0]
            assert len(first_row) > 0
            
            # Check GTIN format
            for header in catalog_data.headers:
                if 'gtin' in header.lower():
                    gtin_value = first_row.get(header, '')
                    assert len(gtin_value) >= 8  # Valid GTIN length
                    break
    
    def test_detect_real_catalog_columns(self):
        """Test column detection on real catalog"""
        catalog_path = 'assets/Catalog_for_Seller_RD997Z-7Z9O6.xlsx'
        
        if not os.path.exists(catalog_path):
            pytest.skip("Wholesaler catalog not found")
        
        parser = CatalogParser()
        catalog_data = parser.parse_file(catalog_path, max_rows=50)
        
        detector = ColumnDetector()
        detection_result = detector.detect_columns(
            catalog_data.headers,
            catalog_data.rows[:20]
        )
        
        # Should detect most columns
        assert len(detection_result.mappings) >= 5
        assert detection_result.confidence_score > 0.5
        
        # Critical fields should be detected
        mapped_fields = {m.standard_field for m in detection_result.mappings}
        assert 'gtin' in mapped_fields or 'sku' in mapped_fields
        assert 'product_name' in mapped_fields
    
    def test_full_workflow_with_real_catalog(self):
        """Test complete workflow with real catalog"""
        catalog_path = 'assets/Catalog_for_Seller_RD997Z-7Z9O6.xlsx'
        
        if not os.path.exists(catalog_path):
            pytest.skip("Wholesaler catalog not found")
        
        # Parse
        parser = CatalogParser()
        catalog_data = parser.parse_file(catalog_path, max_rows=10)
        
        # Detect
        detector = ColumnDetector()
        detection_result = detector.detect_columns(
            catalog_data.headers,
            catalog_data.rows[:10]
        )
        
        # Create mappings
        column_mappings = {m.catalog_column: m.standard_field 
                          for m in detection_result.mappings}
        
        # Verify we can create QogitaProduct objects
        mock_matcher = Mock()
        worker = CatalogScanWorker(
            catalog_data,
            column_mappings,
            'EUR',
            False,
            20.0,
            mock_matcher
        )
        
        products_created = 0
        for row in catalog_data.rows[:5]:
            product = worker._create_qogita_product(row)
            if product:
                products_created += 1
                assert isinstance(product, QogitaProduct)
                assert product.wholesale_price > 0
        
        assert products_created > 0  # At least some products should be created


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
