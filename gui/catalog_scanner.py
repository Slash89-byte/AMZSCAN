"""
Catalog Scanner - Bulk wholesaler catalog analysis

Features:
- Upload CSV/Excel catalog files
- Smart column detection with manual review
- Multi-currency support
- VAT handling options
- Template management
- Bulk Amazon matching and profitability analysis
"""

import sys
import logging
from typing import List, Dict, Optional
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog,
    QTableWidget, QTableWidgetItem, QTextEdit, QProgressBar, QGroupBox,
    QHeaderView, QMessageBox, QComboBox, QCheckBox, QLineEdit, QDialog,
    QDialogButtonBox, QSpinBox, QDoubleSpinBox, QTabWidget, QSplitter
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QFont, QColor

from core.keepa_api import KeepaAPI
from core.enhanced_roi_calculator import EnhancedROICalculator
from utils.product_matcher import ProductMatcher, QogitaProduct, MatchedProduct, export_matched_products_to_csv
from utils.config import Config
from utils.catalog_parser import CatalogParser, CatalogData
from utils.column_detector import ColumnDetector, ColumnMapping, DetectionResult
from utils.template_manager import TemplateManager, WholesalerTemplate

logger = logging.getLogger(__name__)


class ColumnMappingDialog(QDialog):
    """Dialog for reviewing and adjusting column mappings"""
    
    def __init__(self, detection_result: DetectionResult, catalog_headers: List[str], parent=None):
        super().__init__(parent)
        self.detection_result = detection_result
        self.catalog_headers = catalog_headers
        self.mappings = {m.catalog_column: m.standard_field for m in detection_result.mappings}
        
        self.setup_ui()
        self.setWindowTitle("Review Column Mappings")
        self.resize(700, 500)
    
    def setup_ui(self):
        """Setup the dialog UI"""
        layout = QVBoxLayout(self)
        
        # Info label
        info_label = QLabel(
            f"📋 Detected {len(self.detection_result.mappings)} column mappings with "
            f"{self.detection_result.confidence_score:.0%} confidence.\n"
            f"Please review and adjust as needed:"
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Warnings
        if self.detection_result.warnings:
            warnings_text = "⚠️ " + "\n⚠️ ".join(self.detection_result.warnings)
            warnings_label = QLabel(warnings_text)
            warnings_label.setStyleSheet("color: orange;")
            warnings_label.setWordWrap(True)
            layout.addWidget(warnings_label)
        
        # Mapping table
        self.mapping_table = QTableWidget()
        self.mapping_table.setColumnCount(3)
        self.mapping_table.setHorizontalHeaderLabels(['Catalog Column', 'Maps To', 'Confidence'])
        
        # Configure table
        header = self.mapping_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        
        # Populate with detections
        self._populate_table()
        
        layout.addWidget(self.mapping_table)
        
        # Unmapped columns section
        if self.detection_result.unmapped_columns:
            unmapped_label = QLabel(f"❓ Unmapped columns: {', '.join(self.detection_result.unmapped_columns)}")
            unmapped_label.setWordWrap(True)
            layout.addWidget(unmapped_label)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def _populate_table(self):
        """Populate mapping table with detections"""
        # Standard field options for dropdown
        standard_fields = [
            'gtin', 'asin', 'sku', 'product_name', 'brand', 'category',
            'wholesale_price', 'retail_price', 'stock', 'moq', 'weight', 'dimensions',
            '(ignore)'
        ]
        
        # Add mapped columns
        row = 0
        for mapping in self.detection_result.mappings:
            self.mapping_table.insertRow(row)
            
            # Catalog column
            col_item = QTableWidgetItem(mapping.catalog_column)
            col_item.setFlags(col_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.mapping_table.setItem(row, 0, col_item)
            
            # Standard field dropdown
            field_combo = QComboBox()
            field_combo.addItems(standard_fields)
            field_combo.setCurrentText(mapping.standard_field)
            field_combo.currentTextChanged.connect(
                lambda text, r=row: self._update_mapping(r, text)
            )
            self.mapping_table.setCellWidget(row, 1, field_combo)
            
            # Confidence
            conf_item = QTableWidgetItem(f"{mapping.confidence:.0%}")
            conf_item.setFlags(conf_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            
            # Color code by confidence
            if mapping.confidence >= 0.8:
                conf_item.setForeground(QColor('green'))
            elif mapping.confidence >= 0.6:
                conf_item.setForeground(QColor('orange'))
            else:
                conf_item.setForeground(QColor('red'))
            
            self.mapping_table.setItem(row, 2, conf_item)
            
            row += 1
    
    def _update_mapping(self, row: int, new_field: str):
        """Update mapping when user changes dropdown"""
        catalog_column = self.mapping_table.item(row, 0).text()
        
        if new_field == '(ignore)':
            self.mappings.pop(catalog_column, None)
        else:
            self.mappings[catalog_column] = new_field
    
    def get_mappings(self) -> Dict[str, str]:
        """Get final column mappings"""
        return self.mappings


class CatalogScanWorker(QThread):
    """Worker thread for catalog scanning and matching"""
    
    progress_updated = pyqtSignal(int, int, str)  # current, total, message
    scan_completed = pyqtSignal(list)  # List[MatchedProduct]
    log_message = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, catalog_data: CatalogData, column_mappings: Dict[str, str],
                 currency: str, vat_included: bool, vat_rate: float,
                 product_matcher: ProductMatcher):
        super().__init__()
        self.catalog_data = catalog_data
        self.column_mappings = column_mappings
        self.currency = currency
        self.vat_included = vat_included
        self.vat_rate = vat_rate
        self.product_matcher = product_matcher
        self.is_running = True
        self.logger = logging.getLogger(__name__)
    
    def stop(self):
        """Stop the scanning process"""
        self.is_running = False
    
    def run(self):
        """Main scanning logic"""
        try:
            matched_products = []
            total_rows = len(self.catalog_data.rows)
            
            self.log_message.emit(f"🚀 Starting catalog scan: {total_rows} products")
            
            for i, row_data in enumerate(self.catalog_data.rows):
                if not self.is_running:
                    self.log_message.emit("❌ Scan stopped by user")
                    break
                
                # Convert row to Qogita product format
                qogita_product = self._create_qogita_product(row_data)
                
                if not qogita_product:
                    continue
                
                # Update progress
                self.progress_updated.emit(
                    i + 1, total_rows,
                    f"Processing: {qogita_product.name[:50]}..."
                )
                
                # Match with Amazon
                try:
                    matched = self.product_matcher.match_product(qogita_product)
                    
                    if matched:
                        matched_products.append(matched)
                        
                        status = "✅" if matched.match_status == "MATCHED" else "⚠️"
                        self.log_message.emit(
                            f"{status} {qogita_product.gtin}: {matched.match_status} "
                            f"(Profit: €{matched.profit_margin:.2f})"
                        )
                    else:
                        self.log_message.emit(f"❌ {qogita_product.gtin}: No match found")
                
                except Exception as e:
                    self.logger.error(f"Error matching product: {str(e)}")
                    self.log_message.emit(f"❌ Error matching {qogita_product.gtin}: {str(e)}")
            
            self.log_message.emit(f"✅ Scan completed: {len(matched_products)}/{total_rows} products matched")
            self.scan_completed.emit(matched_products)
            
        except Exception as e:
            self.logger.error(f"Error in scan worker: {str(e)}", exc_info=True)
            self.error_occurred.emit(str(e))
    
    def _create_qogita_product(self, row_data: Dict[str, str]) -> Optional[QogitaProduct]:
        """Create QogitaProduct from row data"""
        try:
            # Get mapped values
            gtin = row_data.get(self._get_catalog_column('gtin'), '').strip()
            name = row_data.get(self._get_catalog_column('product_name'), '').strip()
            brand = row_data.get(self._get_catalog_column('brand'), '').strip()
            category = row_data.get(self._get_catalog_column('category'), '').strip()
            
            # Parse price
            price_str = row_data.get(self._get_catalog_column('wholesale_price'), '0').strip()
            wholesale_price = self._parse_price(price_str)
            
            # Adjust for VAT if included
            if self.vat_included and wholesale_price > 0:
                wholesale_price = wholesale_price / (1 + self.vat_rate / 100)
            
            # Get stock
            stock_str = row_data.get(self._get_catalog_column('stock'), '0').strip()
            stock = self._parse_int(stock_str)
            
            # Validate required fields
            if not gtin and not (brand and name):
                return None
            
            if wholesale_price <= 0:
                return None
            
            # Create product
            return QogitaProduct(
                gtin=gtin,
                name=name,
                category=category,
                brand=brand,
                wholesale_price=wholesale_price,
                unit='unit',
                stock=stock,
                suppliers=1,
                product_url='',
                image_url=''
            )
            
        except Exception as e:
            self.logger.error(f"Error creating product from row: {str(e)}")
            return None
    
    def _get_catalog_column(self, standard_field: str) -> str:
        """Get catalog column name for a standard field"""
        for cat_col, std_field in self.column_mappings.items():
            if std_field == standard_field:
                return cat_col
        return ''
    
    def _parse_price(self, price_str: str) -> float:
        """Parse price string to float"""
        try:
            # Remove currency symbols and spaces
            cleaned = price_str.replace('€', '').replace('$', '').replace('£', '').replace(' ', '')
            # Replace comma with dot for decimal
            cleaned = cleaned.replace(',', '.')
            return float(cleaned)
        except:
            return 0.0
    
    def _parse_int(self, int_str: str) -> int:
        """Parse integer string"""
        try:
            return int(int_str.replace(' ', '').replace(',', ''))
        except:
            return 0


class CatalogScannerWindow(QWidget):
    """Main window for catalog scanner"""
    
    def __init__(self):
        super().__init__()
        self.config = Config()
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.keepa_api = KeepaAPI(self.config)
        self.roi_calculator = EnhancedROICalculator()
        self.product_matcher = ProductMatcher(self.keepa_api, self.roi_calculator)
        self.catalog_parser = CatalogParser()
        self.column_detector = ColumnDetector()
        self.template_manager = TemplateManager()
        
        # Data storage
        self.catalog_data: Optional[CatalogData] = None
        self.column_mappings: Dict[str, str] = {}
        self.matched_products: List[MatchedProduct] = []
        self.scan_worker: Optional[CatalogScanWorker] = None
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("📦 Catalog Scanner - Bulk Wholesaler Analysis")
        title.setFont(QFont('Arial', 16, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # File upload section
        upload_group = self._create_upload_section()
        layout.addWidget(upload_group)
        
        # Settings section
        settings_group = self._create_settings_section()
        layout.addWidget(settings_group)
        
        # Column mapping section
        mapping_group = self._create_mapping_section()
        layout.addWidget(mapping_group)
        
        # Progress section
        progress_group = self._create_progress_section()
        layout.addWidget(progress_group)
        
        # Results section
        results_group = self._create_results_section()
        layout.addWidget(results_group, 1)  # Stretch
    
    def _create_upload_section(self) -> QGroupBox:
        """Create file upload section"""
        group = QGroupBox("1️⃣ Upload Catalog File")
        layout = QHBoxLayout(group)
        
        self.file_label = QLabel("No file selected")
        layout.addWidget(self.file_label, 1)
        
        upload_btn = QPushButton("📁 Choose File")
        upload_btn.clicked.connect(self.upload_file)
        layout.addWidget(upload_btn)
        
        return group
    
    def _create_settings_section(self) -> QGroupBox:
        """Create settings section"""
        group = QGroupBox("2️⃣ Configure Settings")
        layout = QHBoxLayout(group)
        
        # Wholesaler name
        layout.addWidget(QLabel("Wholesaler:"))
        self.wholesaler_input = QLineEdit()
        self.wholesaler_input.setPlaceholderText("Enter wholesaler name (for template)")
        layout.addWidget(self.wholesaler_input, 1)
        
        # Currency
        layout.addWidget(QLabel("Currency:"))
        self.currency_combo = QComboBox()
        self.currency_combo.addItems(['EUR', 'USD', 'GBP', 'CHF', 'JPY'])
        layout.addWidget(self.currency_combo)
        
        # VAT handling
        self.vat_checkbox = QCheckBox("Prices include VAT")
        layout.addWidget(self.vat_checkbox)
        
        self.vat_rate_spin = QDoubleSpinBox()
        self.vat_rate_spin.setRange(0, 50)
        self.vat_rate_spin.setValue(20)
        self.vat_rate_spin.setSuffix("%")
        self.vat_rate_spin.setEnabled(False)
        layout.addWidget(self.vat_rate_spin)
        
        self.vat_checkbox.toggled.connect(self.vat_rate_spin.setEnabled)
        
        return group
    
    def _create_mapping_section(self) -> QGroupBox:
        """Create column mapping section"""
        group = QGroupBox("3️⃣ Column Mapping")
        layout = QHBoxLayout(group)
        
        self.mapping_label = QLabel("Upload a file to detect columns")
        layout.addWidget(self.mapping_label, 1)
        
        self.review_mapping_btn = QPushButton("🔍 Review Mapping")
        self.review_mapping_btn.setEnabled(False)
        self.review_mapping_btn.clicked.connect(self.review_mapping)
        layout.addWidget(self.review_mapping_btn)
        
        self.load_template_btn = QPushButton("📋 Load Template")
        self.load_template_btn.clicked.connect(self.load_template)
        layout.addWidget(self.load_template_btn)
        
        self.save_template_btn = QPushButton("💾 Save Template")
        self.save_template_btn.setEnabled(False)
        self.save_template_btn.clicked.connect(self.save_template)
        layout.addWidget(self.save_template_btn)
        
        return group
    
    def _create_progress_section(self) -> QGroupBox:
        """Create progress section"""
        group = QGroupBox("4️⃣ Scan Progress")
        layout = QVBoxLayout(group)
        
        # Control buttons
        btn_layout = QHBoxLayout()
        
        self.scan_btn = QPushButton("🚀 Start Scan")
        self.scan_btn.setEnabled(False)
        self.scan_btn.clicked.connect(self.start_scan)
        btn_layout.addWidget(self.scan_btn)
        
        self.stop_btn = QPushButton("⏹ Stop")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_scan)
        btn_layout.addWidget(self.stop_btn)
        
        self.export_btn = QPushButton("💾 Export Results")
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self.export_results)
        btn_layout.addWidget(self.export_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)
        
        # Log
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        layout.addWidget(self.log_text)
        
        return group
    
    def _create_results_section(self) -> QGroupBox:
        """Create results section"""
        group = QGroupBox("5️⃣ Results")
        layout = QVBoxLayout(group)
        
        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(11)
        self.results_table.setHorizontalHeaderLabels([
            'GTIN', 'Brand', 'Product Name', 'Category', 'Wholesale €',
            'Amazon €', 'Profit €', 'ROI %', 'Stock', 'Status', 'ASIN'
        ])
        
        # Configure table
        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setSortingEnabled(True)
        
        layout.addWidget(self.results_table)
        
        return group
    
    def upload_file(self):
        """Handle file upload"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Catalog File",
            "", "Catalog Files (*.csv *.xlsx *.xls);;All Files (*)"
        )
        
        if not file_path:
            return
        
        try:
            # Parse file
            self.add_log("📂 Parsing catalog file...")
            self.catalog_data = self.catalog_parser.parse_file(file_path)
            
            # Validate
            validation = self.catalog_parser.validate_data(self.catalog_data)
            
            if not validation['is_valid']:
                QMessageBox.critical(self, "Invalid File", "\n".join(validation['errors']))
                return
            
            # Update UI
            filename = Path(file_path).name
            self.file_label.setText(f"✅ {filename} ({self.catalog_data.total_rows} products)")
            
            self.add_log(f"✅ Parsed {self.catalog_data.total_rows} products with {len(self.catalog_data.headers)} columns")
            
            if validation['warnings']:
                for warning in validation['warnings']:
                    self.add_log(f"⚠️ {warning}")
            
            # Auto-detect columns
            self.detect_columns(filename)
            
        except Exception as e:
            self.logger.error(f"Error uploading file: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Upload Error", f"Failed to parse file:\n\n{str(e)}")
    
    def detect_columns(self, filename: str = ""):
        """Detect column mappings"""
        if not self.catalog_data:
            return
        
        try:
            self.add_log("🔍 Detecting column mappings...")
            
            # Check for matching template
            template_name = self.template_manager.find_matching_template(
                self.catalog_data.headers, filename
            )
            
            if template_name:
                self.add_log(f"📋 Found matching template: {template_name}")
                template = self.template_manager.get_template(template_name)
                self.column_mappings = template.column_mappings
                self.currency_combo.setCurrentText(template.currency)
                self.vat_checkbox.setChecked(template.vat_included)
                self.wholesaler_input.setText(template_name)
                
                self.mapping_label.setText(
                    f"✅ Loaded template: {template_name} ({len(self.column_mappings)} mappings)"
                )
            else:
                # Auto-detect
                detection_result = self.column_detector.detect_columns(
                    self.catalog_data.headers,
                    self.catalog_data.rows[:20]
                )
                
                self.column_mappings = {m.catalog_column: m.standard_field 
                                      for m in detection_result.mappings}
                
                # Update currency if detected
                if self.catalog_data.detected_currency:
                    self.currency_combo.setCurrentText(self.catalog_data.detected_currency)
                
                self.mapping_label.setText(
                    f"✅ Detected {len(self.column_mappings)} mappings "
                    f"({detection_result.confidence_score:.0%} confidence)"
                )
                
                if detection_result.warnings:
                    for warning in detection_result.warnings:
                        self.add_log(f"⚠️ {warning}")
            
            # Enable buttons
            self.review_mapping_btn.setEnabled(True)
            self.save_template_btn.setEnabled(True)
            self.scan_btn.setEnabled(len(self.column_mappings) > 0)
            
        except Exception as e:
            self.logger.error(f"Error detecting columns: {str(e)}", exc_info=True)
            self.add_log(f"❌ Error detecting columns: {str(e)}")
    
    def review_mapping(self):
        """Open dialog to review column mappings"""
        if not self.catalog_data:
            return
        
        # Create detection result from current mappings
        mappings = [
            ColumnMapping(cat_col, std_field, 0.8, 'user')
            for cat_col, std_field in self.column_mappings.items()
        ]
        
        unmapped = [h for h in self.catalog_data.headers 
                   if h not in self.column_mappings]
        
        detection_result = DetectionResult(
            mappings=mappings,
            unmapped_columns=unmapped,
            confidence_score=0.8,
            warnings=[]
        )
        
        dialog = ColumnMappingDialog(detection_result, self.catalog_data.headers, self)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.column_mappings = dialog.get_mappings()
            self.mapping_label.setText(f"✅ Updated: {len(self.column_mappings)} mappings")
            self.scan_btn.setEnabled(len(self.column_mappings) > 0)
            self.add_log(f"✅ Column mappings updated")
    
    def load_template(self):
        """Load a saved template"""
        templates = self.template_manager.list_templates()
        
        if not templates:
            QMessageBox.information(self, "No Templates", "No saved templates found.")
            return
        
        # Show selection dialog
        from PyQt6.QtWidgets import QListWidget, QListWidgetItem
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Load Template")
        dialog.resize(500, 400)
        
        layout = QVBoxLayout(dialog)
        
        layout.addWidget(QLabel("Select a template to load:"))
        
        list_widget = QListWidget()
        for template in templates:
            item_text = (f"{template['name']} - {template['currency']} - "
                        f"{template['column_count']} columns "
                        f"(used {template['use_count']} times)")
            list_widget.addItem(item_text)
        
        layout.addWidget(list_widget)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec() == QDialog.DialogCode.Accepted and list_widget.currentRow() >= 0:
            selected_template = templates[list_widget.currentRow()]
            template = self.template_manager.get_template(selected_template['name'])
            
            self.column_mappings = template.column_mappings
            self.currency_combo.setCurrentText(template.currency)
            self.vat_checkbox.setChecked(template.vat_included)
            self.wholesaler_input.setText(template.name)
            
            self.mapping_label.setText(f"✅ Loaded template: {template.name}")
            self.scan_btn.setEnabled(True)
            self.add_log(f"✅ Loaded template: {template.name}")
    
    def save_template(self):
        """Save current mapping as template"""
        if not self.column_mappings:
            QMessageBox.warning(self, "No Mappings", "No column mappings to save.")
            return
        
        wholesaler_name = self.wholesaler_input.text().strip()
        
        if not wholesaler_name:
            wholesaler_name, ok = QInputDialog.getText(
                self, "Save Template", "Enter wholesaler name:"
            )
            if not ok or not wholesaler_name.strip():
                return
            wholesaler_name = wholesaler_name.strip()
        
        # Save template
        metadata = {}
        if self.catalog_data:
            metadata = {
                'file_format': self.catalog_data.file_format,
                'encoding': self.catalog_data.encoding,
                'delimiter': self.catalog_data.detected_separator
            }
        
        success = self.template_manager.save_template(
            name=wholesaler_name,
            column_mappings=self.column_mappings,
            currency=self.currency_combo.currentText(),
            vat_included=self.vat_checkbox.isChecked(),
            metadata=metadata
        )
        
        if success:
            QMessageBox.information(self, "Template Saved", 
                                   f"Template '{wholesaler_name}' saved successfully!")
            self.add_log(f"💾 Saved template: {wholesaler_name}")
        else:
            QMessageBox.critical(self, "Save Error", "Failed to save template.")
    
    def start_scan(self):
        """Start the catalog scanning process"""
        if not self.catalog_data or not self.column_mappings:
            QMessageBox.warning(self, "Not Ready", "Please upload a file and configure mappings first.")
            return
        
        # Validate API key
        if not self.config.get_keepa_api_key():
            QMessageBox.warning(self, "API Key Missing", "Please configure your Keepa API key in Settings.")
            return
        
        # Update UI state
        self.scan_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.export_btn.setEnabled(False)
        self.results_table.setRowCount(0)
        self.matched_products.clear()
        
        # Create and start worker
        self.scan_worker = CatalogScanWorker(
            self.catalog_data,
            self.column_mappings,
            self.currency_combo.currentText(),
            self.vat_checkbox.isChecked(),
            self.vat_rate_spin.value(),
            self.product_matcher
        )
        
        self.scan_worker.progress_updated.connect(self.update_progress)
        self.scan_worker.scan_completed.connect(self.scan_completed)
        self.scan_worker.log_message.connect(self.add_log)
        self.scan_worker.error_occurred.connect(self.scan_error)
        
        self.scan_worker.start()
    
    def stop_scan(self):
        """Stop the scanning process"""
        if self.scan_worker:
            self.scan_worker.stop()
            self.stop_btn.setEnabled(False)
    
    def update_progress(self, current: int, total: int, message: str):
        """Update progress bar"""
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.progress_bar.setFormat(f"{current}/{total} - {message}")
    
    def scan_completed(self, matched_products: List[MatchedProduct]):
        """Handle scan completion"""
        self.matched_products = matched_products
        
        # Update UI state
        self.scan_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.export_btn.setEnabled(len(matched_products) > 0)
        
        # Populate results table
        for product in matched_products:
            self._add_result_row(product)
        
        self.add_log(f"🎉 Scan completed: {len(matched_products)} products matched")
    
    def scan_error(self, error_msg: str):
        """Handle scan error"""
        self.scan_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        
        QMessageBox.critical(self, "Scan Error", f"An error occurred:\n\n{error_msg}")
    
    def _add_result_row(self, product: MatchedProduct):
        """Add a result row to the table"""
        row = self.results_table.rowCount()
        self.results_table.insertRow(row)
        
        qp = product.qogita_product
        
        # Add data
        self.results_table.setItem(row, 0, QTableWidgetItem(qp.gtin))
        self.results_table.setItem(row, 1, QTableWidgetItem(qp.brand))
        self.results_table.setItem(row, 2, QTableWidgetItem(qp.name))
        self.results_table.setItem(row, 3, QTableWidgetItem(qp.category))
        self.results_table.setItem(row, 4, QTableWidgetItem(f"{qp.wholesale_price:.2f}"))
        
        # Amazon price
        amazon_price = f"{product.amazon_price:.2f}" if product.amazon_price else "N/A"
        self.results_table.setItem(row, 5, QTableWidgetItem(amazon_price))
        
        # Profit
        profit = f"{product.profit_margin:.2f}" if product.profit_margin else "N/A"
        profit_item = QTableWidgetItem(profit)
        if product.profit_margin and product.profit_margin > 0:
            profit_item.setForeground(QColor('green'))
        elif product.profit_margin and product.profit_margin < 0:
            profit_item.setForeground(QColor('red'))
        self.results_table.setItem(row, 6, profit_item)
        
        # ROI
        roi = f"{product.roi_percentage:.1f}" if product.roi_percentage else "N/A"
        self.results_table.setItem(row, 7, QTableWidgetItem(roi))
        
        # Stock
        self.results_table.setItem(row, 8, QTableWidgetItem(str(qp.stock)))
        
        # Status
        self.results_table.setItem(row, 9, QTableWidgetItem(product.match_status))
        
        # ASIN
        self.results_table.setItem(row, 10, QTableWidgetItem(product.amazon_asin or "N/A"))
    
    def export_results(self):
        """Export results to CSV"""
        if not self.matched_products:
            QMessageBox.information(self, "No Results", "No results to export.")
            return
        
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Export Results", "catalog_scan_results.csv", "CSV Files (*.csv)"
        )
        
        if filepath:
            try:
                export_matched_products_to_csv(self.matched_products, filepath)
                QMessageBox.information(self, "Export Successful", 
                                       f"Results exported to:\n{filepath}")
                self.add_log(f"💾 Results exported to {filepath}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export:\n\n{str(e)}")
    
    def add_log(self, message: str):
        """Add message to log"""
        self.log_text.append(message)
        # Auto-scroll to bottom
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )


# Import for input dialog
from PyQt6.QtWidgets import QInputDialog
