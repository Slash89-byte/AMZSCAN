"""
Qogita Brand Scanner - Bulk brand analysis with profitability calculations

This module provides a GUI for scanning entire brands from Qogita wholesale catalog
and performing bulk profitability analysis against Amazon prices.
"""

import sys
import logging
from typing import List, Dict
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QLabel,
    QTableWidget, QTableWidgetItem, QTextEdit, QProgressBar, QGroupBox,
    QHeaderView, QMessageBox, QComboBox, QSpinBox, QCheckBox, QFileDialog,
    QTabWidget, QSplitter
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QTimer
from PyQt6.QtGui import QFont, QPalette, QColor

from core.qogita_api import QogitaAPI
from core.keepa_api import KeepaAPI
from core.enhanced_roi_calculator import EnhancedROICalculator
from utils.product_matcher import ProductMatcher, QogitaProduct, MatchedProduct, export_matched_products_to_csv
from utils.config import Config


class QogitaScanWorker(QThread):
    """Worker thread for Qogita brand scanning and matching"""
    
    # Signals for progress tracking
    progress_updated = pyqtSignal(int, int, str)
    scan_completed = pyqtSignal(list)  # List of matched products
    product_matched = pyqtSignal(object)  # Individual product matched (real-time)
    log_message = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, brand_names: List[str], qogita_api: QogitaAPI, 
                 product_matcher: ProductMatcher):
        super().__init__()
        self.brand_names = brand_names
        self.qogita_api = qogita_api
        self.product_matcher = product_matcher
        self.logger = logging.getLogger(__name__)
        
    def run(self):
        """Run the brand scanning and matching process"""
        try:
            all_matched_products = []
            
            for i, brand_name in enumerate(self.brand_names):
                self.progress_updated.emit(i + 1, len(self.brand_names), f"Scanning brand: {brand_name}")
                self.log_message.emit(f"Starting scan for brand: {brand_name}")
                
                # Get products from Qogita for this brand
                qogita_products = self._scan_brand(brand_name)
                
                if qogita_products:
                    self.log_message.emit(f"Found {len(qogita_products)} products for {brand_name}")
                    
                    # Match with Amazon data one by one for real-time updates
                    self.log_message.emit(f"Matching {len(qogita_products)} products with Amazon...")
                    
                    matched_products = []
                    for j, qogita_product in enumerate(qogita_products):
                        # Update progress for individual product
                        product_progress = f"Matching {brand_name}: {j+1}/{len(qogita_products)} - {qogita_product.name[:50]}..."
                        self.progress_updated.emit(i + 1, len(self.brand_names), product_progress)
                        
                        # Match individual product
                        matched_product = self.product_matcher.match_single_product(qogita_product)
                        matched_products.append(matched_product)
                        
                        # Emit real-time result
                        self.product_matched.emit(matched_product)
                        
                        # Small delay to prevent UI freezing
                        self.msleep(10)  # 10ms delay
                    
                    all_matched_products.extend(matched_products)
                    self.log_message.emit(f"Completed matching for {brand_name}: {len(matched_products)} products")
                else:
                    self.log_message.emit(f"No products found for brand: {brand_name}")
            
            self.log_message.emit(f"Scan completed! Total products processed: {len(all_matched_products)}")
            self.scan_completed.emit(all_matched_products)
            
        except Exception as e:
            error_msg = f"Error during brand scanning: {str(e)}"
            self.logger.error(error_msg)
            self.error_occurred.emit(error_msg)
    
    def _scan_brand(self, brand_name: str) -> List[QogitaProduct]:
        """Scan products for a specific brand"""
        try:
            # Get raw products from Qogita API
            raw_products = self.qogita_api.search_products_by_brand(brand_name)
            
            # Convert to QogitaProduct objects
            qogita_products = []
            for product_data in raw_products:
                try:
                    # Parse the new Qogita API format
                    qogita_product = QogitaProduct(
                        gtin=str(product_data.get('gtin', '')),
                        name=product_data.get('name', ''),
                        category=product_data.get('category', ''),
                        brand=product_data.get('brand', ''),
                        wholesale_price=float(product_data.get('wholesale_price', 0)),
                        unit=str(product_data.get('unit', '')),
                        stock=int(product_data.get('stock_quantity', 0)),
                        suppliers=int(product_data.get('supplier_count', 0)),
                        product_url=product_data.get('product_url', ''),
                        image_url=product_data.get('image_url', '')
                    )
                    
                    # Only include products with valid GTIN and price
                    if qogita_product.gtin and qogita_product.wholesale_price > 0:
                        qogita_products.append(qogita_product)
                        
                except (ValueError, KeyError) as e:
                    self.logger.warning(f"Error parsing product data: {str(e)}")
                    continue
            
            return qogita_products
            
        except Exception as e:
            self.logger.error(f"Error scanning brand {brand_name}: {str(e)}")
            return []


class ProductTableWidget(QTableWidget):
    """Enhanced table widget for displaying matched products"""
    
    def __init__(self):
        super().__init__()
        self.setup_table()
        
    def setup_table(self):
        """Setup the product table"""
        headers = [
            'GTIN', 'Brand', 'Product Name', 'Category', 'Wholesale €', 
            'Amazon €', 'Profit €', 'ROI %', 'Confidence', 'Stock', 'Status', 'ASIN'
        ]
        
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)
        
        # Configure table properties
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(True)
        
        # Set column widths
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # GTIN
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Brand
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)          # Product Name
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Category
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Wholesale
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Amazon
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # Profit
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)  # ROI
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)  # Confidence
        header.setSectionResizeMode(9, QHeaderView.ResizeMode.ResizeToContents)  # Stock
        header.setSectionResizeMode(10, QHeaderView.ResizeMode.ResizeToContents) # Status
        header.setSectionResizeMode(11, QHeaderView.ResizeMode.ResizeToContents) # ASIN
    
    def add_matched_product(self, matched_product: MatchedProduct):
        """Add a matched product to the table"""
        row = self.rowCount()
        self.insertRow(row)
        
        qp = matched_product.qogita_product
        
        # Add data to columns
        self.setItem(row, 0, QTableWidgetItem(qp.gtin))
        self.setItem(row, 1, QTableWidgetItem(qp.brand))
        self.setItem(row, 2, QTableWidgetItem(qp.name))
        self.setItem(row, 3, QTableWidgetItem(qp.category))
        self.setItem(row, 4, QTableWidgetItem(f"{qp.wholesale_price:.2f}"))
        
        # Amazon price
        amazon_price_item = QTableWidgetItem(
            f"{matched_product.amazon_price:.2f}" if matched_product.amazon_price else "N/A"
        )
        self.setItem(row, 5, amazon_price_item)
        
        # Profit margin
        profit_item = QTableWidgetItem(
            f"{matched_product.profit_margin:.2f}" if matched_product.profit_margin else "N/A"
        )
        if matched_product.profit_margin and matched_product.profit_margin > 0:
            profit_item.setBackground(QColor(144, 238, 144))  # Light green
        elif matched_product.profit_margin and matched_product.profit_margin < 0:
            profit_item.setBackground(QColor(255, 182, 193))  # Light red
        self.setItem(row, 6, profit_item)
        
        # ROI percentage
        roi_item = QTableWidgetItem(
            f"{matched_product.roi_percentage:.1f}%" if matched_product.roi_percentage else "N/A"
        )
        if matched_product.roi_percentage and matched_product.roi_percentage >= 15:
            roi_item.setBackground(QColor(144, 238, 144))  # Light green
        elif matched_product.roi_percentage and matched_product.roi_percentage < 15:
            roi_item.setBackground(QColor(255, 182, 193))  # Light red
        self.setItem(row, 7, roi_item)
        
        # Match confidence
        confidence_item = QTableWidgetItem(f"{matched_product.match_confidence}%")
        if matched_product.match_confidence >= 90:
            confidence_item.setBackground(QColor(144, 238, 144))  # Light green
        elif matched_product.match_confidence >= 70:
            confidence_item.setBackground(QColor(255, 255, 224))  # Light yellow
        elif matched_product.match_confidence > 0:
            confidence_item.setBackground(QColor(255, 182, 193))  # Light red
        self.setItem(row, 8, confidence_item)
        
        self.setItem(row, 9, QTableWidgetItem(str(qp.stock)))
        
        # Status with color coding
        status_item = QTableWidgetItem(matched_product.match_status)
        if matched_product.match_status == "matched":
            status_item.setBackground(QColor(144, 238, 144))  # Light green
        elif matched_product.match_status == "matched_by_name":
            status_item.setBackground(QColor(173, 216, 230))  # Light blue
        elif matched_product.match_status == "not_found":
            status_item.setBackground(QColor(255, 255, 224))  # Light yellow
        elif matched_product.match_status == "no_price":
            status_item.setBackground(QColor(255, 222, 173))  # Light orange
        elif matched_product.match_status == "gtin_invalid":
            status_item.setBackground(QColor(255, 182, 193))  # Light red
        elif matched_product.match_status == "error":
            status_item.setBackground(QColor(255, 182, 193))  # Light red
        self.setItem(row, 10, status_item)
        
        self.setItem(row, 11, QTableWidgetItem(matched_product.amazon_asin or "N/A"))


class QogitaScannerWindow(QWidget):
    """Main window for Qogita brand scanner"""
    
    def __init__(self):
        super().__init__()
        self.config = Config()
        self.logger = logging.getLogger(__name__)
        
        # Get Qogita credentials from config
        qogita_settings = self.config.get('qogita_settings', {})
        qogita_email = qogita_settings.get('email')
        qogita_password = qogita_settings.get('password')
        
        if not qogita_email or not qogita_password:
            self.logger.error("Qogita credentials not found in config")
            # Initialize with empty credentials - will show error in UI
            self.qogita_api = None
        else:
            # Initialize APIs
            self.qogita_api = QogitaAPI(qogita_email, qogita_password)
            
        # Get Keepa API key
        keepa_api_key = self.config.get_keepa_api_key()
        if not keepa_api_key:
            self.logger.error("Keepa API key not found in config")
            self.keepa_api = None
        else:
            self.keepa_api = KeepaAPI(keepa_api_key)
            
        self.roi_calculator = EnhancedROICalculator()
        
        # Only create product matcher if we have both APIs
        if self.qogita_api and self.keepa_api:
            self.product_matcher = ProductMatcher(self.keepa_api, self.roi_calculator)
        else:
            self.product_matcher = None
        
        # Data storage
        self.matched_products: List[MatchedProduct] = []
        
        # Worker thread
        self.scan_worker = None
        
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        """Setup the user interface"""
        self.setWindowTitle("Qogita Brand Scanner - Bulk Profitability Analysis")
        self.setGeometry(100, 100, 1400, 800)
        
        # Main layout
        main_layout = QVBoxLayout()
        
        # Title and description
        title_label = QLabel("🧴 Qogita Brand Scanner")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label)
        
        desc_label = QLabel("Scan entire brands from Qogita wholesale catalog and analyze profitability on Amazon")
        desc_label.setStyleSheet("color: #666; margin-bottom: 10px;")
        main_layout.addWidget(desc_label)
        
        # Create tabs
        tab_widget = QTabWidget()
        
        # Scan Configuration Tab
        scan_tab = QWidget()
        scan_layout = QVBoxLayout(scan_tab)
        
        # Brand input section
        brand_group = QGroupBox("Brand Configuration")
        brand_layout = QVBoxLayout()
        
        # Brand name input
        brand_input_layout = QHBoxLayout()
        brand_input_layout.addWidget(QLabel("Brand Names:"))
        self.brand_input = QLineEdit()
        self.brand_input.setPlaceholderText("Enter brand names separated by commas (e.g., L'Oréal, Wella, Schwarzkopf)")
        brand_input_layout.addWidget(self.brand_input)
        brand_layout.addLayout(brand_input_layout)
        
        # Quick brand buttons
        quick_brands_layout = QHBoxLayout()
        quick_brands_layout.addWidget(QLabel("Quick Select:"))
        
        quick_brands = ["L'Oréal", "Wella", "Schwarzkopf", "Maybelline", "Garnier"]
        for brand in quick_brands:
            btn = QPushButton(brand)
            btn.clicked.connect(lambda checked, b=brand: self.add_brand_to_input(b))
            quick_brands_layout.addWidget(btn)
        
        brand_layout.addLayout(quick_brands_layout)
        brand_group.setLayout(brand_layout)
        scan_layout.addWidget(brand_group)
        
        # Filter settings
        filter_group = QGroupBox("Profitability Filters")
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel("Min ROI %:"))
        self.min_roi_spin = QSpinBox()
        self.min_roi_spin.setRange(0, 100)
        self.min_roi_spin.setValue(15)
        filter_layout.addWidget(self.min_roi_spin)
        
        filter_layout.addWidget(QLabel("Min Price €:"))
        self.min_price_spin = QSpinBox()
        self.min_price_spin.setRange(0, 1000)
        self.min_price_spin.setValue(10)
        filter_layout.addWidget(self.min_price_spin)
        
        self.show_all_checkbox = QCheckBox("Show all products (not just profitable)")
        filter_layout.addWidget(self.show_all_checkbox)
        
        filter_layout.addStretch()
        filter_group.setLayout(filter_layout)
        scan_layout.addWidget(filter_group)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.scan_button = QPushButton("🔍 Start Brand Scan")
        self.scan_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                font-size: 14px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        button_layout.addWidget(self.scan_button)
        
        self.stop_button = QPushButton("⏹ Stop Scan")
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)
        
        self.export_button = QPushButton("📁 Export Results")
        self.export_button.setEnabled(False)
        button_layout.addWidget(self.export_button)
        
        button_layout.addStretch()
        scan_layout.addLayout(button_layout)
        
        # Progress section
        progress_group = QGroupBox("Scan Progress")
        progress_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        progress_layout.addWidget(self.progress_bar)
        
        self.progress_label = QLabel("Ready to scan")
        progress_layout.addWidget(self.progress_label)
        
        progress_group.setLayout(progress_layout)
        scan_layout.addWidget(progress_group)
        
        scan_layout.addStretch()
        tab_widget.addTab(scan_tab, "Scan Configuration")
        
        # Results Tab
        results_tab = QWidget()
        results_layout = QVBoxLayout(results_tab)
        
        # Results summary
        summary_layout = QHBoxLayout()
        self.total_products_label = QLabel("Total Products: 0")
        self.matched_products_label = QLabel("Matched: 0")
        self.profitable_products_label = QLabel("Profitable: 0")
        
        summary_layout.addWidget(self.total_products_label)
        summary_layout.addWidget(self.matched_products_label)
        summary_layout.addWidget(self.profitable_products_label)
        summary_layout.addStretch()
        
        results_layout.addLayout(summary_layout)
        
        # Product table
        self.product_table = ProductTableWidget()
        results_layout.addWidget(self.product_table)
        
        tab_widget.addTab(results_tab, "Results")
        
        # Logs Tab
        logs_tab = QWidget()
        logs_layout = QVBoxLayout(logs_tab)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        logs_layout.addWidget(self.log_text)
        
        # Clear logs button
        clear_logs_btn = QPushButton("Clear Logs")
        clear_logs_btn.clicked.connect(self.log_text.clear)
        logs_layout.addWidget(clear_logs_btn)
        
        tab_widget.addTab(logs_tab, "Logs")
        
        main_layout.addWidget(tab_widget)
        self.setLayout(main_layout)
    
    def setup_connections(self):
        """Setup signal connections"""
        self.scan_button.clicked.connect(self.start_scan)
        self.stop_button.clicked.connect(self.stop_scan)
        self.export_button.clicked.connect(self.export_results)
        
        # Product matcher signals
        self.product_matcher.progress_updated.connect(self.update_progress)
        self.product_matcher.product_matched.connect(self.add_matched_product)
        
    def add_brand_to_input(self, brand_name: str):
        """Add a brand name to the input field"""
        current_text = self.brand_input.text().strip()
        if current_text:
            if brand_name not in current_text:
                self.brand_input.setText(f"{current_text}, {brand_name}")
        else:
            self.brand_input.setText(brand_name)
    
    def start_scan(self):
        """Start the brand scanning process"""
        # Check if APIs are properly initialized
        if not self.qogita_api or not self.product_matcher or not self.keepa_api:
            missing_apis = []
            if not self.qogita_api:
                missing_apis.append("Qogita API credentials")
            if not self.keepa_api:
                missing_apis.append("Keepa API key")
                
            QMessageBox.critical(
                self, 
                "Configuration Error", 
                f"Missing configuration: {', '.join(missing_apis)}\n\n"
                "Please add your credentials to config.json:\n"
                '{\n'
                '  "keepa_api_key": "your-keepa-key",\n'
                '  "qogita_settings": {\n'
                '    "email": "your-email@example.com",\n'
                '    "password": "your-password"\n'
                '  }\n'
                '}'
            )
            return
            
        brand_text = self.brand_input.text().strip()
        if not brand_text:
            QMessageBox.warning(self, "No Brands", "Please enter at least one brand name to scan.")
            return
        
        # Parse brand names
        brand_names = [name.strip() for name in brand_text.split(',') if name.strip()]
        
        # Clear previous results
        self.matched_products.clear()
        self.product_table.setRowCount(0)
        self.log_text.clear()
        
        # Update UI state
        self.scan_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.export_button.setEnabled(False)
        
        # Create and start worker thread
        self.scan_worker = QogitaScanWorker(brand_names, self.qogita_api, self.product_matcher)
        self.scan_worker.progress_updated.connect(self.update_progress)
        self.scan_worker.scan_completed.connect(self.scan_completed)
        self.scan_worker.product_matched.connect(self.add_matched_product_realtime)  # Real-time updates
        self.scan_worker.log_message.connect(self.add_log_message)
        self.scan_worker.error_occurred.connect(self.handle_error)
        
        self.scan_worker.start()
        
        self.add_log_message(f"Starting scan for brands: {', '.join(brand_names)}")
    
    def stop_scan(self):
        """Stop the scanning process"""
        if self.scan_worker and self.scan_worker.isRunning():
            self.scan_worker.terminate()
            self.scan_worker.wait()
        
        self.scan_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.add_log_message("Scan stopped by user")
    
    def update_progress(self, current: int, total: int, status: str):
        """Update progress bar and status"""
        if total > 0:
            progress = int((current / total) * 100)
            self.progress_bar.setValue(progress)
        
        self.progress_label.setText(f"{status} ({current}/{total})")
    
    def add_matched_product_realtime(self, matched_product: MatchedProduct):
        """Add a matched product to the results in real-time"""
        self.matched_products.append(matched_product)
        
        # Apply filters if needed
        show_all = self.show_all_checkbox.isChecked()
        if not show_all:
            min_roi = self.min_roi_spin.value()
            min_price = self.min_price_spin.value()
            
            # Filter by ROI
            if matched_product.roi_percentage is None or matched_product.roi_percentage < min_roi:
                return
            
            # Filter by price
            if matched_product.amazon_price is None or matched_product.amazon_price < min_price:
                return
        
        # Add to table immediately
        self.product_table.add_matched_product(matched_product)
        
        # Update summary counters in real-time
        total_products = len(self.matched_products)
        profitable_count = sum(1 for p in self.matched_products 
                              if p.roi_percentage and p.roi_percentage >= 15)
        matched_count = sum(1 for p in self.matched_products 
                           if p.match_status in ["matched", "matched_by_name"])
        
        self.total_products_label.setText(f"Total Products: {total_products}")
        self.profitable_products_label.setText(f"Profitable (15%+ ROI): {profitable_count}")
        self.matched_products_label.setText(f"Amazon Matches: {matched_count}")
        
        # Scroll to the new item
        self.product_table.scrollToBottom()
    
    def add_matched_product(self, matched_product: MatchedProduct):
        """Add a matched product to the results (legacy method for bulk operations)"""
        self.matched_products.append(matched_product)
        
        # Apply filters if needed
        show_all = self.show_all_checkbox.isChecked()
        if not show_all:
            min_roi = self.min_roi_spin.value()
            min_price = self.min_price_spin.value()
            
            if (matched_product.roi_percentage is None or 
                matched_product.amazon_price is None or
                matched_product.roi_percentage < min_roi or
                matched_product.amazon_price < min_price):
                self.update_summary()
                return
        
        # Add to table
        self.product_table.add_matched_product(matched_product)
        self.update_summary()
    
    def scan_completed(self, all_matched_products: List[MatchedProduct]):
        """Handle scan completion"""
        self.scan_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.export_button.setEnabled(True)
        
        self.progress_bar.setValue(100)
        self.progress_label.setText("Scan completed")
        
        self.update_summary()
        self.add_log_message(f"Scan completed! Processed {len(all_matched_products)} products.")
    
    def update_summary(self):
        """Update the results summary"""
        total = len(self.matched_products)
        matched = len([p for p in self.matched_products if p.match_status == "matched"])
        profitable = len([p for p in self.matched_products 
                         if p.roi_percentage and p.roi_percentage >= self.min_roi_spin.value()])
        
        self.total_products_label.setText(f"Total Products: {total}")
        self.matched_products_label.setText(f"Matched: {matched}")
        self.profitable_products_label.setText(f"Profitable: {profitable}")
    
    def add_log_message(self, message: str):
        """Add a message to the log"""
        self.log_text.append(f"[{QTimer().remainingTime()}] {message}")
    
    def handle_error(self, error_message: str):
        """Handle error messages"""
        self.add_log_message(f"ERROR: {error_message}")
        QMessageBox.critical(self, "Scan Error", error_message)
        
        # Reset UI state
        self.scan_button.setEnabled(True)
        self.stop_button.setEnabled(False)
    
    def export_results(self):
        """Export results to CSV"""
        if not self.matched_products:
            QMessageBox.information(self, "No Results", "No results to export.")
            return
        
        # Get save file path
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Export Results", "qogita_scan_results.csv", "CSV Files (*.csv)"
        )
        
        if filepath:
            try:
                export_matched_products_to_csv(self.matched_products, filepath)
                QMessageBox.information(self, "Export Successful", f"Results exported to {filepath}")
                self.add_log_message(f"Results exported to {filepath}")
            except Exception as e:
                error_msg = f"Error exporting results: {str(e)}"
                QMessageBox.critical(self, "Export Error", error_msg)
                self.add_log_message(error_msg)
