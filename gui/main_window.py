"""
Main window for the Amazon Profitability Analyzer
"""

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QLineEdit, QPushButton, QTextEdit, 
                            QGroupBox, QGridLayout, QMessageBox, QProgressBar)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

from core.amazon_fees import AmazonFeesCalculator
from core.keepa_api import KeepaAPI
from core.roi_calculator import ROICalculator
from utils.config import Config

class AnalysisWorker(QThread):
    """Worker thread for product analysis to prevent GUI freezing"""
    analysis_complete = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, asin, cost_price, config):
        super().__init__()
        self.asin = asin
        self.cost_price = cost_price
        self.config = config
    
    def run(self):
        try:
            # Initialize components
            keepa_api = KeepaAPI(self.config.get('keepa_api_key'))
            fees_calc = AmazonFeesCalculator('france')
            roi_calc = ROICalculator()
            
            # Get product data from Keepa
            product_data = keepa_api.get_product_data(self.asin)
            if not product_data:
                error_msg = (
                    f"Failed to fetch product data for ASIN: {self.asin}\n\n"
                    "Possible causes:\n"
                    "• Invalid ASIN\n"
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
                error_msg = (
                    f"No current price available for ASIN: {self.asin}\n\n"
                    "The product might be:\n"
                    "• Out of stock\n"
                    "• Not sold by Amazon\n"
                    "• Price data temporarily unavailable\n\n"
                    "Try a different ASIN or check later."
                )
                self.error_occurred.emit(error_msg)
                return
            
            # Calculate fees
            current_price = product_data.get('current_price', 0)
            amazon_fees = fees_calc.calculate_fees(current_price, product_data.get('weight', 0.5))
            
            # Calculate ROI
            roi_data = roi_calc.calculate_roi(
                cost_price=self.cost_price,
                selling_price=current_price,
                amazon_fees=amazon_fees
            )
            
            # Compile results
            results = {
                'asin': self.asin,
                'product_title': product_data.get('title', 'Unknown'),
                'current_price': current_price,
                'cost_price': self.cost_price,
                'amazon_fees': amazon_fees,
                'profit': roi_data['profit'],
                'roi_percentage': roi_data['roi_percentage'],
                'is_profitable': roi_data['roi_percentage'] >= self.config.get('min_roi_threshold', 15)
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
    
    def create_input_section(self):
        group = QGroupBox("Product Analysis")
        layout = QGridLayout(group)
        
        # ASIN input
        layout.addWidget(QLabel("ASIN:"), 0, 0)
        self.asin_input = QLineEdit()
        self.asin_input.setPlaceholderText("Enter Amazon ASIN (e.g., B08N5WRWNW)")
        layout.addWidget(self.asin_input, 0, 1)
        
        # Cost price input
        layout.addWidget(QLabel("Your Cost Price (€):"), 1, 0)
        self.cost_input = QLineEdit()
        self.cost_input.setPlaceholderText("Enter your cost price in euros")
        layout.addWidget(self.cost_input, 1, 1)
        
        # Analyze button
        self.analyze_button = QPushButton("Analyze Profitability")
        self.analyze_button.clicked.connect(self.analyze_product)
        layout.addWidget(self.analyze_button, 2, 0, 1, 2)
        
        return group
    
    def create_results_section(self):
        group = QGroupBox("Analysis Results")
        layout = QVBoxLayout(group)
        
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setMaximumHeight(300)
        layout.addWidget(self.results_text)
        
        return group
    
    def analyze_product(self):
        asin = self.asin_input.text().strip()
        cost_price_text = self.cost_input.text().strip()
        
        # Validation
        if not asin:
            QMessageBox.warning(self, "Input Error", "Please enter an ASIN")
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
        
        # Start analysis
        self.start_analysis(asin, cost_price)
    
    def start_analysis(self, asin, cost_price):
        self.analyze_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.status_label.setText("Analyzing product...")
        self.results_text.clear()
        
        # Start worker thread
        self.worker = AnalysisWorker(asin, cost_price, self.config)
        self.worker.analysis_complete.connect(self.on_analysis_complete)
        self.worker.error_occurred.connect(self.on_analysis_error)
        self.worker.start()
    
    def on_analysis_complete(self, results):
        self.analyze_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText("Analysis complete!")
        
        # Format results
        roi_color = "green" if results['is_profitable'] else "red"
        profitability_text = "✅ PROFITABLE" if results['is_profitable'] else "❌ NOT PROFITABLE"
        
        results_html = f"""
        <h3>Product Analysis Results</h3>
        <p><strong>ASIN:</strong> {results['asin']}</p>
        <p><strong>Product:</strong> {results['product_title']}</p>
        <hr>
        <p><strong>Current Amazon Price:</strong> €{results['current_price']:.2f}</p>
        <p><strong>Your Cost Price:</strong> €{results['cost_price']:.2f}</p>
        <p><strong>Amazon Fees:</strong> €{results['amazon_fees']:.2f}</p>
        <p><strong>Profit:</strong> €{results['profit']:.2f}</p>
        <hr>
        <h2 style="color: {roi_color}">ROI: {results['roi_percentage']:.1f}%</h2>
        <h3 style="color: {roi_color}">{profitability_text}</h3>
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
