"""
Enhanced main window for Amazon Profitability Analyzer with Priority 1 features:
- Product image display
- Basic Keepa price chart
- Enhanced results layout with visual indicators
- Product details panel
"""

import sys
import os
from io import BytesIO
from typing import Optional, Dict, Any
import requests
from PIL import Image
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates
from datetime import datetime, timedelta

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QLabel, QLineEdit, QPushButton, QTextEdit, QGroupBox, 
    QGridLayout, QMessageBox, QProgressBar, QScrollArea,
    QFrame, QTabWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QSizePolicy
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize, QTimer
from PyQt6.QtGui import QFont, QAction, QPixmap, QIcon, QPalette, QColor

from core.enhanced_amazon_fees import EnhancedAmazonFeesCalculator
from core.keepa_api import KeepaAPI
from core.enhanced_roi_calculator import EnhancedROICalculator
from utils.config import Config
from utils.identifiers import detect_and_validate_identifier
from gui.config_dialog import ConfigurationDialog


class ProductImageWidget(QLabel):
    """Widget for displaying product images with loading states"""
    
    def __init__(self):
        super().__init__()
        self.setMinimumSize(200, 200)
        self.setMaximumSize(300, 300)
        self.setScaledContents(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                border: 2px solid #ddd;
                border-radius: 8px;
                background-color: #f9f9f9;
                padding: 10px;
            }
        """)
        self.show_placeholder()
    
    def show_placeholder(self):
        """Show placeholder when no image is available"""
        self.setText("📦\n\nProduct Image\nLoading...")
        self.setStyleSheet("""
            QLabel {
                border: 2px dashed #ccc;
                border-radius: 8px;
                background-color: #f9f9f9;
                color: #666;
                font-size: 14px;
                padding: 10px;
            }
        """)
    
    def show_error(self):
        """Show error state when image fails to load"""
        self.setText("❌\n\nImage\nUnavailable")
        self.setStyleSheet("""
            QLabel {
                border: 2px solid #ffdddd;
                border-radius: 8px;
                background-color: #fff5f5;
                color: #cc0000;
                font-size: 14px;
                padding: 10px;
            }
        """)
    
    def set_image(self, image_data: bytes):
        """Set product image from image data"""
        try:
            # Load image with PIL
            pil_image = Image.open(BytesIO(image_data))
            
            # Convert to RGB if necessary
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')
            
            # Resize to fit widget
            pil_image.thumbnail((280, 280), Image.Resampling.LANCZOS)
            
            # Convert to QPixmap
            # Save to bytes first
            img_bytes = BytesIO()
            pil_image.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            
            pixmap = QPixmap()
            pixmap.loadFromData(img_bytes.read())
            
            self.setPixmap(pixmap)
            self.setStyleSheet("""
                QLabel {
                    border: 2px solid #4CAF50;
                    border-radius: 8px;
                    background-color: white;
                    padding: 5px;
                }
            """)
            
        except Exception as e:
            print(f"Error setting image: {e}")
            self.show_error()


class KeepaChartWidget(QWidget):
    """Widget for displaying Keepa price charts"""
    
    def __init__(self):
        super().__init__()
        self.setMinimumHeight(250)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Create matplotlib figure
        self.figure = Figure(figsize=(8, 4), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        
        self.setLayout(layout)
        self.show_placeholder()
    
    def show_placeholder(self):
        """Show placeholder chart"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.text(0.5, 0.5, '📊\n\nPrice Chart\nLoading...', 
                ha='center', va='center', transform=ax.transAxes,
                fontsize=16, color='#666')
        ax.set_xticks([])
        ax.set_yticks([])
        self.canvas.draw()
    
    def plot_price_history(self, price_history: list, title: str = "Price History"):
        """Plot price history data"""
        try:
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            
            if not price_history or len(price_history) < 2:
                ax.text(0.5, 0.5, 'No price history\navailable', 
                        ha='center', va='center', transform=ax.transAxes,
                        fontsize=14, color='#666')
                ax.set_xticks([])
                ax.set_yticks([])
                self.canvas.draw()
                return
            
            # Parse price history (assuming format: [timestamp, price, timestamp, price, ...])
            timestamps = []
            prices = []
            
            for i in range(0, len(price_history), 2):
                if i + 1 < len(price_history):
                    # Keepa timestamps are in minutes since Keepa epoch
                    timestamp = price_history[i]
                    price = price_history[i + 1]
                    
                    if price != -1:  # -1 means no data
                        # Convert Keepa timestamp to datetime
                        # Keepa epoch is 2011-01-01
                        keepa_epoch = datetime(2011, 1, 1)
                        actual_time = keepa_epoch + timedelta(minutes=timestamp)
                        timestamps.append(actual_time)
                        prices.append(price / 100.0)  # Keepa prices are in cents
            
            if not timestamps:
                ax.text(0.5, 0.5, 'No valid price data\navailable', 
                        ha='center', va='center', transform=ax.transAxes,
                        fontsize=14, color='#666')
                ax.set_xticks([])
                ax.set_yticks([])
                self.canvas.draw()
                return
            
            # Plot the data
            ax.plot(timestamps, prices, linewidth=2, color='#2196F3', marker='o', markersize=3)
            ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
            ax.set_xlabel('Date', fontsize=12)
            ax.set_ylabel('Price (€)', fontsize=12)
            ax.grid(True, alpha=0.3)
            
            # Format x-axis
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
            ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
            
            # Rotate x-axis labels
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
            
            # Add price annotations for first and last points
            if len(prices) > 1:
                ax.annotate(f'€{prices[0]:.2f}', 
                           xy=(timestamps[0], prices[0]), 
                           xytext=(5, 5), textcoords='offset points',
                           fontsize=10, color='#666')
                ax.annotate(f'€{prices[-1]:.2f}', 
                           xy=(timestamps[-1], prices[-1]), 
                           xytext=(5, 5), textcoords='offset points',
                           fontsize=10, color='#666')
            
            # Tight layout
            self.figure.tight_layout()
            self.canvas.draw()
            
        except Exception as e:
            print(f"Error plotting price history: {e}")
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            ax.text(0.5, 0.5, f'Chart Error:\n{str(e)}', 
                    ha='center', va='center', transform=ax.transAxes,
                    fontsize=12, color='#cc0000')
            ax.set_xticks([])
            ax.set_yticks([])
            self.canvas.draw()


class ProductDetailsWidget(QWidget):
    """Widget for displaying product details"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("Product Details")
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        # Details table
        self.details_table = QTableWidget(0, 2)
        self.details_table.setHorizontalHeaderLabels(["Property", "Value"])
        self.details_table.horizontalHeader().setStretchLastSection(True)
        self.details_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.details_table.setAlternatingRowColors(True)
        self.details_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.details_table)
        
        self.setLayout(layout)
    
    def add_detail(self, property_name: str, value: str):
        """Add a detail row to the table"""
        row = self.details_table.rowCount()
        self.details_table.insertRow(row)
        self.details_table.setItem(row, 0, QTableWidgetItem(property_name))
        self.details_table.setItem(row, 1, QTableWidgetItem(str(value)))
    
    def clear_details(self):
        """Clear all details"""
        self.details_table.setRowCount(0)
    
    def update_product_details(self, product_data: Dict[str, Any]):
        """Update product details from product data"""
        self.clear_details()
        
        if not product_data:
            self.add_detail("Status", "No product data available")
            return
        
        # Basic information
        self.add_detail("ASIN", product_data.get('asin', 'N/A'))
        self.add_detail("Title", product_data.get('title', 'N/A'))
        
        # Pricing information
        current_price = product_data.get('current_price', 0)
        if current_price > 0:
            self.add_detail("Current Price", f"€{current_price:.2f}")
        else:
            self.add_detail("Current Price", "Not available")
        
        # Reviews and rating
        rating = product_data.get('rating', 0)
        if rating > 0:
            stars = "⭐" * int(rating) + "☆" * (5 - int(rating))
            self.add_detail("Rating", f"{rating:.1f}/5 {stars}")
        else:
            self.add_detail("Rating", "No rating")
        
        review_count = product_data.get('review_count', 0)
        self.add_detail("Reviews", f"{review_count:,} reviews")
        
        # Sales rank
        sales_rank = product_data.get('sales_rank', 0)
        if sales_rank > 0:
            self.add_detail("Sales Rank", f"#{sales_rank:,}")
        else:
            self.add_detail("Sales Rank", "Not available")
        
        # Category
        category = product_data.get('main_category', 'Unknown')
        self.add_detail("Category", category)
        
        # Physical properties
        weight = product_data.get('weight', 0)
        if weight > 0:
            self.add_detail("Weight", f"{weight:.2f} kg")
        
        # Stock status
        in_stock = product_data.get('in_stock', False)
        stock_status = "✅ In Stock" if in_stock else "❌ Out of Stock"
        self.add_detail("Stock Status", stock_status)
        
        # Fee category
        fee_category = product_data.get('fee_category', 'default')
        self.add_detail("Fee Category", fee_category.title())


class EnhancedAnalysisWorker(QThread):
    """Enhanced worker thread for product analysis with image and chart data"""
    analysis_complete = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    image_loaded = pyqtSignal(bytes)
    chart_data_ready = pyqtSignal(list, str)
    
    def __init__(self, product_id: str, cost_price: float, config: Config):
        super().__init__()
        self.product_id = product_id
        self.cost_price = cost_price
        self.config = config
    
    def run(self):
        try:
            # Initialize components
            keepa_api = KeepaAPI(self.config.get('api_settings.keepa_api_key'))
            fees_calc = EnhancedAmazonFeesCalculator('france', self.config)
            roi_calc = EnhancedROICalculator(self.config)
            
            # Get product data from Keepa
            api_response = keepa_api.get_product_data(self.product_id)
            
            if not api_response or not api_response.get('success', False):
                error_msg = api_response.get('error', 'Failed to fetch product data from Keepa API') if api_response else 'Failed to fetch product data from Keepa API'
                self.error_occurred.emit(error_msg)
                return
            
            # Extract product data from the API response
            product_data = api_response.get('data', {})
            
            # Store product data for use in other methods
            self.current_product_data = product_data
            
            # Extract raw data for enhanced features
            raw_data = product_data.get('raw_data', {})
            
            # Try to load product image
            self.load_product_image(raw_data)
            
            # Try to extract price history for chart
            self.extract_price_history(raw_data, product_data.get('title', 'Product'))
            
            # Perform comprehensive ROI analysis
            current_price = product_data.get('current_price', 0)
            if current_price <= 0:
                self.error_occurred.emit("Product price not available")
                return
            
            fee_category = product_data.get('fee_category', 'default')
            product_weight = product_data.get('weight', 0.5)
            
            roi_data = roi_calc.calculate_comprehensive_roi(
                cost_price=self.cost_price,
                selling_price=current_price,
                weight_kg=product_weight,
                category=fee_category,
                keepa_data=raw_data
            )
            
            # Get identifier info
            identifier_result = detect_and_validate_identifier(self.product_id)
            
            # Compile comprehensive results
            results = {
                'product_id': self.product_id,
                'identifier_type': identifier_result['identifier_type'],
                'identifier_valid': identifier_result['is_valid'],
                'product_data': product_data,
                'analysis_results': roi_data,
                'raw_keepa_data': raw_data
            }
            
            self.analysis_complete.emit(results)
            
        except Exception as e:
            self.error_occurred.emit(f"Analysis error: {str(e)}")
    
    def load_product_image(self, raw_data: Dict[str, Any]):
        """Load product image from Amazon"""
        try:
            # Try to get image URL from the parsed product data first
            if hasattr(self, 'current_product_data'):
                image_url = self.current_product_data.get('image_url')
                if image_url:
                    # Fetch image
                    response = requests.get(image_url, timeout=10)
                    if response.status_code == 200:
                        self.image_loaded.emit(response.content)
                        return
            
            # Fallback: Try to get image URL from Keepa imagesCSV data
            images_csv = raw_data.get('imagesCSV')
            if images_csv and isinstance(images_csv, str):
                # imagesCSV contains comma-separated image filenames
                image_filenames = images_csv.split(',')
                if image_filenames:
                    # Get the first image
                    image_filename = image_filenames[0].strip()
                    if image_filename:
                        # Construct Amazon image URL
                        image_url = f"https://images-na.ssl-images-amazon.com/images/I/{image_filename}"
                        
                        # Fetch image
                        response = requests.get(image_url, timeout=10)
                        if response.status_code == 200:
                            self.image_loaded.emit(response.content)
        except Exception as e:
            print(f"Error loading product image: {e}")
    
    def extract_price_history(self, raw_data: Dict[str, Any], title: str):
        """Extract price history for chart"""
        try:
            # Try to get price history from the parsed product data first
            if hasattr(self, 'current_product_data'):
                price_history = self.current_product_data.get('price_history', [])
                if price_history:
                    # Convert to the format expected by the chart widget
                    chart_data = []
                    for point in price_history:
                        chart_data.extend([point['timestamp'], int(point['price'] * 100)])
                    self.chart_data_ready.emit(chart_data, f"Price History - {title}")
                    return
            
            # Fallback: Try to extract from raw CSV data
            csv_data = raw_data.get('csv', [])
            if isinstance(csv_data, list) and len(csv_data) > 1:
                # CSV[1] contains Amazon price history
                price_history = csv_data[1]
                if price_history:
                    self.chart_data_ready.emit(price_history, f"Price History - {title}")
            elif isinstance(csv_data, dict):
                # Handle dict format as fallback
                price_history = csv_data.get(1, [])
                if price_history:
                    self.chart_data_ready.emit(price_history, f"Price History - {title}")
        except Exception as e:
            print(f"Error extracting price history: {e}")


class EnhancedMainWindow(QMainWindow):
    """Enhanced main window with Priority 1 features"""
    
    def __init__(self):
        super().__init__()
        self.config = Config()
        self.worker = None
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("Amazon Profitability Analyzer - Enhanced")
        self.setGeometry(100, 100, 1400, 900)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Central widget with splitter layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        # Title
        title_label = QLabel("Amazon Product Profitability Analyzer - Enhanced")
        title_font = QFont("Arial", 18, QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("padding: 15px; background-color: #f0f0f0; border-radius: 8px; margin-bottom: 10px;")
        main_layout.addWidget(title_label)
        
        # Input section
        input_group = self.create_input_section()
        main_layout.addWidget(input_group)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        # Main content splitter
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel (Product info and details)
        left_panel = self.create_left_panel()
        main_splitter.addWidget(left_panel)
        
        # Right panel (Analysis results and charts)
        right_panel = self.create_right_panel()
        main_splitter.addWidget(right_panel)
        
        # Set splitter proportions
        main_splitter.setSizes([400, 1000])
        main_layout.addWidget(main_splitter)
        
        # Status section
        self.status_label = QLabel("Ready to analyze products...")
        self.status_label.setStyleSheet("padding: 8px; background-color: #e8f5e8; border-radius: 4px;")
        main_layout.addWidget(self.status_label)
    
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
    
    def create_input_section(self):
        """Create enhanced input section"""
        group = QGroupBox("Product Analysis")
        group.setMaximumHeight(150)
        layout = QGridLayout(group)
        
        # Product identifier input
        layout.addWidget(QLabel("Product ID:"), 0, 0)
        self.product_input = QLineEdit()
        self.product_input.setPlaceholderText("Enter ASIN, GTIN, EAN, or UPC (e.g., B0BQBXBW88)")
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
        self.analyze_button = QPushButton("🔍 Analyze Profitability")
        self.analyze_button.clicked.connect(self.analyze_product)
        self.analyze_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        layout.addWidget(self.analyze_button, 3, 0, 1, 2)
        
        return group
    
    def create_left_panel(self):
        """Create left panel with product image and details"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Product image
        image_group = QGroupBox("Product Image")
        image_layout = QVBoxLayout(image_group)
        self.product_image = ProductImageWidget()
        image_layout.addWidget(self.product_image)
        layout.addWidget(image_group)
        
        # Product details
        details_group = QGroupBox("Product Information")
        details_layout = QVBoxLayout(details_group)
        self.product_details = ProductDetailsWidget()
        details_layout.addWidget(self.product_details)
        layout.addWidget(details_group)
        
        return panel
    
    def create_right_panel(self):
        """Create right panel with results and charts"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Create tab widget for results and charts
        tab_widget = QTabWidget()
        
        # Analysis Results Tab
        results_tab = QWidget()
        results_layout = QVBoxLayout(results_tab)
        
        results_group = QGroupBox("Analysis Results")
        results_group_layout = QVBoxLayout(results_group)
        
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setMinimumHeight(400)
        results_group_layout.addWidget(self.results_text)
        
        results_layout.addWidget(results_group)
        tab_widget.addTab(results_tab, "📊 Analysis Results")
        
        # Price Chart Tab
        chart_tab = QWidget()
        chart_layout = QVBoxLayout(chart_tab)
        
        chart_group = QGroupBox("Price History")
        chart_group_layout = QVBoxLayout(chart_group)
        
        self.keepa_chart = KeepaChartWidget()
        chart_group_layout.addWidget(self.keepa_chart)
        
        chart_layout.addWidget(chart_group)
        tab_widget.addTab(chart_tab, "📈 Price Chart")
        
        layout.addWidget(tab_widget)
        
        return panel
    
    def on_product_input_changed(self):
        """Handle product input changes"""
        product_code = self.product_input.text().strip()
        
        if not product_code:
            self.identifier_label.setText("")
            self.identifier_label.setStyleSheet("color: gray; font-size: 11px;")
            return
        
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
        """Start enhanced product analysis"""
        product_id = self.product_input.text().strip()
        cost_price_text = self.cost_input.text().strip()
        
        if not product_id:
            QMessageBox.warning(self, "Input Error", "Please enter a product ID (ASIN, EAN, UPC, or GTIN)")
            return
        
        result = detect_and_validate_identifier(product_id)
        if not result['is_valid']:
            QMessageBox.warning(self, "Invalid Product ID", 
                               f"The product ID '{product_id}' is not valid. Please check the format.")
            return
        
        try:
            cost_price = float(cost_price_text)
            if cost_price <= 0:
                raise ValueError("Cost price must be positive")
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Please enter a valid cost price (e.g., 8.50)")
            return
        
        api_key = self.config.get('keepa_api_key')
        if not api_key:
            QMessageBox.warning(self, "Configuration Error", 
                               "Keepa API key not configured. Please go to Configuration > General to set it up.")
            return
        
        self.start_enhanced_analysis(product_id, cost_price)
    
    def start_enhanced_analysis(self, product_id: str, cost_price: float):
        """Start enhanced analysis with image and chart loading"""
        # Reset UI state
        self.product_image.show_placeholder()
        self.keepa_chart.show_placeholder()
        self.product_details.clear_details()
        self.results_text.setText("🔄 Analyzing product...\n\nFetching data from Keepa API...")
        
        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.analyze_button.setEnabled(False)
        self.status_label.setText(f"Analyzing {product_id}...")
        
        # Start worker thread
        self.worker = EnhancedAnalysisWorker(product_id, cost_price, self.config)
        self.worker.analysis_complete.connect(self.on_enhanced_analysis_complete)
        self.worker.error_occurred.connect(self.on_analysis_error)
        self.worker.image_loaded.connect(self.on_image_loaded)
        self.worker.chart_data_ready.connect(self.on_chart_data_ready)
        self.worker.start()
    
    def on_enhanced_analysis_complete(self, results: Dict[str, Any]):
        """Handle enhanced analysis completion"""
        self.progress_bar.setVisible(False)
        self.analyze_button.setEnabled(True)
        self.status_label.setText("Enhanced analysis complete!")
        
        # Update product details
        product_data = results.get('product_data', {})
        self.product_details.update_product_details(product_data)
        
        # Format enhanced results
        analysis = results.get('analysis_results', {})
        self.format_enhanced_results(results, analysis)
    
    def on_image_loaded(self, image_data: bytes):
        """Handle product image loading"""
        self.product_image.set_image(image_data)
    
    def on_chart_data_ready(self, price_history: list, title: str):
        """Handle chart data loading"""
        self.keepa_chart.plot_price_history(price_history, title)
    
    def format_enhanced_results(self, results: Dict[str, Any], analysis: Dict[str, Any]):
        """Format enhanced analysis results with visual indicators"""
        product_data = results.get('product_data', {})
        
        # Extract key metrics
        roi_percentage = analysis.get('roi_percentage', 0)
        profit = analysis.get('profit', 0)
        profitability_score = analysis.get('profitability_score', 0)
        is_profitable = analysis.get('is_profitable', False)
        
        # Color coding
        profit_color = "#4CAF50" if is_profitable else "#f44336"
        profit_icon = "✅" if is_profitable else "❌"
        profit_text = "PROFITABLE" if is_profitable else "NOT PROFITABLE"
        
        # Build enhanced HTML results
        html = f"""
        <style>
        .header {{ background-color: {profit_color}; color: white; padding: 15px; border-radius: 8px; text-align: center; margin-bottom: 20px; }}
        .metric {{ background-color: #f5f5f5; padding: 10px; margin: 5px 0; border-radius: 5px; border-left: 4px solid #2196F3; }}
        .fee-item {{ padding: 5px 0; border-bottom: 1px solid #eee; }}
        .profitable {{ color: #4CAF50; font-weight: bold; }}
        .unprofitable {{ color: #f44336; font-weight: bold; }}
        .score {{ font-size: 24px; font-weight: bold; text-align: center; }}
        </style>
        
        <div class="header">
            <h2>{profit_icon} {profit_text}</h2>
            <div class="score">ROI: {roi_percentage:.1f}% | Score: {profitability_score:.0f}/100</div>
        </div>
        
        <h3>📋 Product Information</h3>
        <div class="metric">
            <strong>Product:</strong> {product_data.get('title', 'Unknown Product')}<br>
            <strong>Product ID:</strong> {results.get('product_id', 'N/A')} ({results.get('identifier_type', 'Unknown')})<br>
            <strong>Current Price:</strong> €{product_data.get('current_price', 0):.2f}<br>
            <strong>Your Cost:</strong> €{analysis.get('original_cost_price', 0):.2f}
        </div>
        
        <h3>💰 Financial Analysis</h3>
        <div class="metric">
            <strong>Net Proceeds:</strong> €{analysis.get('net_proceeds', 0):.2f}<br>
            <strong>Total Amazon Fees:</strong> €{analysis.get('total_amazon_fees', 0):.2f}<br>
            <strong>Net Profit:</strong> <span class="{'profitable' if profit >= 0 else 'unprofitable'}">€{profit:.2f}</span><br>
            <strong>Profit Margin:</strong> {analysis.get('profit_margin', 0):.1f}%
        </div>
        """
        
        # Add detailed fee breakdown
        fee_breakdown = analysis.get('amazon_fees_breakdown', {})
        if fee_breakdown:
            html += """
            <h3>📊 Detailed Fee Breakdown</h3>
            <div class="metric">
            """
            
            fee_details = [
                ('Referral Fee', fee_breakdown.get('referral_fee', 0)),
                ('FBA Fee', fee_breakdown.get('fba_fee', 0)),
                ('Storage Fee', fee_breakdown.get('storage_fee', 0)),
                ('Prep Fee', fee_breakdown.get('prep_fee', 0)),
                ('Inbound Shipping', fee_breakdown.get('inbound_shipping', 0)),
                ('Digital Services', fee_breakdown.get('digital_services', 0)),
                ('Misc Fee', fee_breakdown.get('misc_fee', 0)),
                ('VAT on Fees', fee_breakdown.get('vat_on_fees', 0))
            ]
            
            for fee_name, fee_amount in fee_details:
                if fee_amount > 0:
                    html += f'<div class="fee-item"><strong>{fee_name}:</strong> €{fee_amount:.2f}</div>'
            
            html += "</div>"
        
        # Add calculation notes
        notes = analysis.get('calculation_notes', [])
        if notes:
            html += """
            <h3>📝 Calculation Notes</h3>
            <div class="metric">
            <ul>
            """
            for note in notes:
                html += f"<li>{note}</li>"
            html += """
            </ul>
            </div>
            """
        
        # Add break-even analysis if unprofitable
        if not is_profitable:
            try:
                # Quick break-even calculation
                cost_price = analysis.get('original_cost_price', 0)
                total_fees = analysis.get('total_amazon_fees', 0)
                target_roi = 20.0
                
                # Simple break-even: (cost * (1 + roi/100) + fees) / (1 - fees_percentage)
                break_even_price = (cost_price * (1 + target_roi/100) + total_fees) * 1.1  # Rough estimate
                
                html += f"""
                <h3>🎯 Break-Even Analysis</h3>
                <div class="metric">
                    <strong>For {target_roi}% ROI, you need:</strong><br>
                    Minimum Selling Price: €{break_even_price:.2f}<br>
                    Current Gap: €{break_even_price - product_data.get('current_price', 0):.2f} too low
                </div>
                """
            except:
                pass
        
        self.results_text.setHtml(html)
    
    def on_analysis_error(self, error_message: str):
        """Handle analysis errors"""
        self.progress_bar.setVisible(False)
        self.analyze_button.setEnabled(True)
        self.status_label.setText(f"Analysis failed: {error_message}")
        
        self.results_text.setHtml(f"""
            <div style="background-color: #ffebee; color: #c62828; padding: 20px; border-radius: 8px; text-align: center;">
                <h3>❌ Analysis Failed</h3>
                <p><strong>Error:</strong> {error_message}</p>
                <p>Please check your inputs and API configuration.</p>
            </div>
        """)
        
        QMessageBox.critical(self, "Analysis Error", f"Analysis failed:\n\n{error_message}")
    
    def open_configuration_dialog(self):
        """Open configuration dialog"""
        dialog = ConfigurationDialog(self, self.config)
        dialog.configuration_saved.connect(self.on_configuration_saved)
        dialog.exec()
    
    def on_configuration_saved(self):
        """Handle configuration updates"""
        self.config = Config()
        self.status_label.setText("Configuration updated successfully!")
        QMessageBox.information(self, "Configuration", "Settings updated successfully!")
    
    def show_about_dialog(self):
        """Show about dialog"""
        about_text = """
        <h3>Amazon Profitability Analyzer - Enhanced</h3>
        <p>Version 2.0</p>
        <p>A comprehensive tool for analyzing Amazon product profitability with enhanced features:</p>
        <ul>
        <li>🖼️ Product image display</li>
        <li>📈 Interactive Keepa price charts</li>
        <li>📊 Enhanced visual results</li>
        <li>📋 Detailed product information</li>
        <li>💰 Comprehensive fee calculations</li>
        <li>🎯 Break-even analysis</li>
        </ul>
        <p>For support and updates, visit our GitHub repository.</p>
        """
        QMessageBox.about(self, "About Amazon Profitability Analyzer", about_text)


if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    window = EnhancedMainWindow()
    window.show()
    sys.exit(app.exec())
