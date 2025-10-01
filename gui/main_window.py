"""
Main window for the Amazon Profitability Analyzer
"""

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QLineEdit, QPushButton, QTextEdit, 
                            QGroupBox, QGridLayout, QMessageBox, QProgressBar,
                            QMenuBar, QMenu)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QAction

from core.enhanced_amazon_fees import EnhancedAmazonFeesCalculator
from core.keepa_api import KeepaAPI
from core.enhanced_roi_calculator import EnhancedROICalculator
from utils.config import Config
from utils.identifiers import detect_and_validate_identifier
from gui.config_dialog import ConfigurationDialog

class AnalysisWorker(QThread):
    """Worker thread for product analysis to prevent GUI freezing"""
    analysis_complete = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, product_id, cost_price, config):
        super().__init__()
        self.product_id = product_id
        self.cost_price = cost_price
        self.config = config
    
    def run(self):
        try:
            # Initialize components with configuration
            keepa_api = KeepaAPI(self.config.get('keepa_api_key'))
            fees_calc = EnhancedAmazonFeesCalculator('france', self.config)
            roi_calc = EnhancedROICalculator(self.config)
            
            # Get product data from Keepa (now supports multiple identifier types)
            product_data = keepa_api.get_product_data(self.product_id)
            if not product_data:
                # Detect identifier type for better error message
                result = detect_and_validate_identifier(self.product_id)
                identifier_type = result['identifier_type']
                error_msg = (
                    f"Failed to fetch product data for {identifier_type}: {self.product_id}\n\n"
                    "Possible causes:\n"
                    f"• Invalid or non-existent {identifier_type}\n"
                    "• Product not available in France marketplace\n"
                    "• Keepa API key issues\n"
                    "• API rate limit exceeded\n"
                    "• Network connectivity problems"
                )
                self.error_occurred.emit(error_msg)
                return
            
            # Validate price data
            current_price = product_data.get('current_price', 0)
            if current_price <= 0:
                identifier_result = detect_and_validate_identifier(self.product_id)
                identifier_type = identifier_result['identifier_type']
                error_msg = (
                    f"No current Buy Box price available for {identifier_type}: {self.product_id}\n\n"
                    "The product might be:\n"
                    "• Out of stock\n"
                    "• Not sold by Amazon\n"
                    "• Buy Box price data temporarily unavailable\n\n"
                    f"Try a different {identifier_type} or check later."
                )
                self.error_occurred.emit(error_msg)
                return
            
            # Calculate comprehensive ROI using enhanced calculator
            current_price = product_data.get('current_price', 0)
            fee_category = product_data.get('fee_category', 'default')
            product_weight = product_data.get('weight', 0.5)
            
            # Use comprehensive ROI calculation with Keepa data
            roi_data = roi_calc.calculate_comprehensive_roi(
                cost_price=self.cost_price,
                selling_price=current_price,
                weight_kg=product_weight,
                category=fee_category,
                keepa_data=product_data.get('raw_data')  # Pass raw Keepa data for dimensions
            )
            
            # Get identifier type information
            identifier_result = detect_and_validate_identifier(self.product_id)
            
            # Compile results with enhanced data
            results = {
                'product_id': self.product_id,
                'identifier_type': identifier_result['identifier_type'],
                'asin': product_data.get('asin', self.product_id),  # Use ASIN from response if available
                'product_title': product_data.get('title', 'Unknown'),
                'current_price': current_price,
                'cost_price': self.cost_price,
                'amazon_fees': roi_data['total_amazon_fees'],  # Use total fees from enhanced calculation
                'profit': roi_data['profit'],
                'roi_percentage': roi_data['roi_percentage'],
                'profit_margin': roi_data['profit_margin'],
                'profitability_score': roi_data['profitability_score'],
                'is_profitable': roi_data['is_profitable'],
                'enhanced_analysis': roi_data,  # Include full enhanced analysis
                'calculation_notes': roi_data['calculation_notes']
            }
            
            self.analysis_complete.emit(results)
            
        except Exception as e:
            self.error_occurred.emit(f"Analysis error: {str(e)}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = Config()
        self.worker = None
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("Amazon Profitability Analyzer")
        self.setGeometry(100, 100, 800, 600)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        layout = QVBoxLayout(central_widget)
        
        # Title
        title_label = QLabel("Amazon Product Profitability Analyzer")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Input section
        input_group = self.create_input_section()
        layout.addWidget(input_group)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Results section
        results_group = self.create_results_section()
        layout.addWidget(results_group)
        
        # Status section
        self.status_label = QLabel("Ready to analyze products...")
        layout.addWidget(self.status_label)
    
    def create_menu_bar(self):
        """Create the main menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        # Configuration action
        config_action = QAction("Configuration...", self)
        config_action.setShortcut("Ctrl+P")
        config_action.triggered.connect(self.open_configuration_dialog)
        file_menu.addAction(config_action)
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        # About action
        about_action = QAction("About...", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)
    
    def open_configuration_dialog(self):
        """Open the configuration dialog"""
        dialog = ConfigurationDialog(self, self.config)
        dialog.configuration_saved.connect(self.on_configuration_saved)
        dialog.exec()
    
    def on_configuration_saved(self):
        """Handle configuration saved event"""
        # Reload configuration
        self.config = Config()
        self.status_label.setText("Configuration updated successfully!")
        QMessageBox.information(self, "Configuration", "Settings have been updated and will be applied immediately.")
    
    def show_about_dialog(self):
        """Show about dialog"""
        about_text = """
        <h3>Amazon Profitability Analyzer</h3>
        <p>Version 1.0</p>
        <p>A comprehensive tool for analyzing Amazon product profitability 
        using Keepa API data and accurate fee calculations.</p>
        <p><b>Features:</b></p>
        <ul>
        <li>Real-time product data from Keepa API</li>
        <li>Accurate Amazon France marketplace fees</li>
        <li>VAT handling for European markets</li>
        <li>ROI calculation and profitability analysis</li>
        <li>Configurable business model settings</li>
        </ul>
        <p>For support and updates, visit our GitHub repository.</p>
        """
        QMessageBox.about(self, "About Amazon Profitability Analyzer", about_text)
    
    def create_input_section(self):
        group = QGroupBox("Product Analysis")
        layout = QGridLayout(group)
        
        # Product identifier input (supports multiple formats)
        layout.addWidget(QLabel("Product ID:"), 0, 0)
        self.product_input = QLineEdit()
        self.product_input.setPlaceholderText("Enter ASIN, GTIN, EAN, or UPC (e.g., B0BQBXBW88, 4003994155486)")
        self.product_input.textChanged.connect(self.on_product_input_changed)
        layout.addWidget(self.product_input, 0, 1)
        
        # Identifier validation feedback
        self.identifier_label = QLabel("")
        self.identifier_label.setStyleSheet("color: gray; font-size: 11px;")
        layout.addWidget(self.identifier_label, 1, 1)
        
        # Cost price input
        layout.addWidget(QLabel("Your Cost Price (€):"), 2, 0)
        self.cost_input = QLineEdit()
        self.cost_input.setPlaceholderText("Enter your cost price in euros")
        layout.addWidget(self.cost_input, 2, 1)
        
        # Analyze button
        self.analyze_button = QPushButton("Analyze Profitability")
        self.analyze_button.clicked.connect(self.analyze_product)
        layout.addWidget(self.analyze_button, 3, 0, 1, 2)
        
        return group
    
    def create_results_section(self):
        group = QGroupBox("Analysis Results")
        layout = QVBoxLayout(group)
        
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setMaximumHeight(300)
        layout.addWidget(self.results_text)
        
        return group
    
    def on_product_input_changed(self):
        """Handle product input changes and provide real-time validation feedback"""
        product_code = self.product_input.text().strip()
        
        if not product_code:
            self.identifier_label.setText("")
            self.identifier_label.setStyleSheet("color: gray; font-size: 11px;")
            return
        
        # Detect and validate identifier
        result = detect_and_validate_identifier(product_code)
        
        if result['is_valid']:
            identifier_type = result['identifier_type']
            formatted_code = result['formatted_code']
            self.identifier_label.setText(f"✓ Valid {identifier_type}: {formatted_code}")
            self.identifier_label.setStyleSheet("color: green; font-size: 11px;")
        elif result['identifier_type'] != "UNKNOWN":
            identifier_type = result['identifier_type']
            self.identifier_label.setText(f"⚠ Invalid {identifier_type} (check format)")
            self.identifier_label.setStyleSheet("color: orange; font-size: 11px;")
        else:
            self.identifier_label.setText("❌ Unknown identifier format")
            self.identifier_label.setStyleSheet("color: red; font-size: 11px;")
    
    def analyze_product(self):
        product_id = self.product_input.text().strip()
        cost_price_text = self.cost_input.text().strip()
        
        # Validation - check if product ID is provided
        if not product_id:
            QMessageBox.warning(self, "Input Error", "Please enter a product identifier (ASIN, GTIN, EAN, or UPC)")
            return
        
        # Validate the product identifier
        result = detect_and_validate_identifier(product_id)
        if not result['is_valid']:
            QMessageBox.warning(self, "Input Error", 
                              f"Invalid {result['identifier_type']} format. Please check your input.")
            return
        
        # All supported identifier types can be used with Keepa API
        if not result['can_use_for_lookup']:
            QMessageBox.warning(self, "Unsupported Format", 
                              f"The {result['identifier_type']} format cannot be used for product lookup. "
                              f"Please use ASIN, EAN, UPC, or GTIN.")
            return
        
        try:
            cost_price = float(cost_price_text)
            if cost_price <= 0:
                raise ValueError("Cost price must be positive")
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Please enter a valid cost price")
            return
        
        # Check API key
        if not self.config.get('keepa_api_key'):
            QMessageBox.warning(self, "Configuration Error", 
                              "Keepa API key not configured. Please check settings.")
            return
        
        # Start analysis with validated product identifier
        product_id = result['normalized_code']
        self.start_analysis(product_id, cost_price)
    
    def start_analysis(self, product_id, cost_price):
        self.analyze_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.status_label.setText("Analyzing product...")
        self.results_text.clear()
        
        # Start worker thread
        self.worker = AnalysisWorker(product_id, cost_price, self.config)
        self.worker.analysis_complete.connect(self.on_analysis_complete)
        self.worker.error_occurred.connect(self.on_analysis_error)
        self.worker.start()
    
    def on_analysis_complete(self, results):
        self.analyze_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText("Analysis complete!")
        
        # Format results with enhanced information
        roi_color = "green" if results['is_profitable'] else "red"
        profitability_text = "✅ PROFITABLE" if results['is_profitable'] else "❌ NOT PROFITABLE"
        
        # Get enhanced analysis data
        enhanced = results.get('enhanced_analysis', {})
        
        # Build detailed fee breakdown
        fee_breakdown = enhanced.get('amazon_fees_breakdown', {})
        fee_details = ""
        if fee_breakdown:
            fee_details = f"""
            <h4>📋 Detailed Fee Breakdown:</h4>
            <ul>
                <li>Referral Fee: €{fee_breakdown.get('referral_fee', 0):.2f}</li>
                <li>FBA Fee: €{fee_breakdown.get('fba_fee', 0):.2f}</li>
                <li>Storage Fee: €{fee_breakdown.get('storage_fee', 0):.2f}</li>
                <li>Prep Fee: €{fee_breakdown.get('prep_fee', 0):.2f}</li>
                <li>Inbound Shipping: €{fee_breakdown.get('inbound_shipping', 0):.2f}</li>
                <li>Digital Services: €{fee_breakdown.get('digital_services', 0):.2f}</li>
                <li>Misc Fee: €{fee_breakdown.get('misc_fee', 0):.2f}</li>
                <li>VAT on Fees: €{fee_breakdown.get('vat_on_fees', 0):.2f}</li>
            </ul>
            """
        
        # Build calculation notes
        notes_html = ""
        notes = results.get('calculation_notes', [])
        if notes:
            notes_html = f"""
            <h4>📝 Calculation Notes:</h4>
            <ul>
                {''.join([f'<li>{note}</li>' for note in notes])}
            </ul>
            """
        
        # Additional metrics
        profit_margin = results.get('profit_margin', 0)
        profitability_score = results.get('profitability_score', 0)
        
        results_html = f"""
        <h3>🔍 Product Analysis Results</h3>
        <p><strong>Product ID:</strong> {results['product_id']} ({results['identifier_type']})</p>
        <p><strong>Product:</strong> {results['product_title']}</p>
        <hr>
        <h4>💰 Financial Analysis:</h4>
        <p><strong>Current Buy Box Price:</strong> €{results['current_price']:.2f}</p>
        <p><strong>Your Cost Price:</strong> €{results['cost_price']:.2f}</p>
        <p><strong>Total Amazon Fees:</strong> €{results['amazon_fees']:.2f}</p>
        <p><strong>Net Profit:</strong> €{results['profit']:.2f}</p>
        <hr>
        <h2 style="color: {roi_color}">📊 ROI: {results['roi_percentage']:.1f}%</h2>
        <h3>📈 Profit Margin: {profit_margin:.1f}%</h3>
        <h3>⭐ Profitability Score: {profitability_score:.1f}/100</h3>
        <h3 style="color: {roi_color}">{profitability_text}</h3>
        {fee_details}
        {notes_html}
        """
        
        self.results_text.setHtml(results_html)
    
    def on_analysis_error(self, error_message):
        self.analyze_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText("Analysis failed!")
        
        QMessageBox.critical(self, "Analysis Error", error_message)
        self.results_text.setPlainText(f"Error: {error_message}")
    
    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            self.worker.quit()
            self.worker.wait()
        event.accept()
