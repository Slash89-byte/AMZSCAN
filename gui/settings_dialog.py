"""
Settings Configuration Dialog

Provides a comprehensive settings interface for configuring API keys,
thresholds, and other application settings.
"""

import json
import os
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
                             QGroupBox, QLabel, QLineEdit, QPushButton, 
                             QSpinBox, QDoubleSpinBox, QCheckBox, QComboBox,
                             QTextEdit, QMessageBox, QFormLayout, QWidget)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class SettingsDialog(QDialog):
    """Settings configuration dialog"""
    
    def __init__(self, config_path="config.json", parent=None):
        super().__init__(parent)
        self.config_path = config_path
        self.config = self.load_config()
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self):
        """Set up the settings dialog UI"""
        self.setWindowTitle("⚙️ Application Settings")
        self.setModal(True)
        self.resize(600, 500)
        
        layout = QVBoxLayout(self)
        
        # Create tab widget
        tab_widget = QTabWidget()
        
        # API Settings Tab
        api_tab = self.create_api_tab()
        tab_widget.addTab(api_tab, "🔑 API Settings")
        
        # Analysis Settings Tab
        analysis_tab = self.create_analysis_tab()
        tab_widget.addTab(analysis_tab, "📊 Analysis Settings")
        
        # Qogita Settings Tab
        qogita_tab = self.create_qogita_tab()
        tab_widget.addTab(qogita_tab, "🏪 Qogita Settings")
        
        # UI Settings Tab
        ui_tab = self.create_ui_tab()
        tab_widget.addTab(ui_tab, "🎨 UI Settings")
        
        layout.addWidget(tab_widget)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.test_btn = QPushButton("🧪 Test APIs")
        self.test_btn.clicked.connect(self.test_apis)
        button_layout.addWidget(self.test_btn)
        
        button_layout.addStretch()
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        self.save_btn = QPushButton("💾 Save Settings")
        self.save_btn.clicked.connect(self.save_settings)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        button_layout.addWidget(self.save_btn)
        
        layout.addLayout(button_layout)
    
    def create_api_tab(self) -> QWidget:
        """Create API settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Keepa API Settings
        keepa_group = QGroupBox("Keepa API Configuration")
        keepa_layout = QFormLayout()
        
        self.keepa_api_key = QLineEdit()
        self.keepa_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.keepa_api_key.setPlaceholderText("Enter your Keepa API key")
        keepa_layout.addRow("API Key:", self.keepa_api_key)
        
        self.amazon_marketplace = QComboBox()
        self.amazon_marketplace.addItems(["france", "germany", "italy", "spain", "uk", "usa"])
        keepa_layout.addRow("Marketplace:", self.amazon_marketplace)
        
        self.request_timeout = QSpinBox()
        self.request_timeout.setRange(10, 120)
        self.request_timeout.setSuffix(" seconds")
        keepa_layout.addRow("Request Timeout:", self.request_timeout)
        
        self.max_retries = QSpinBox()
        self.max_retries.setRange(1, 10)
        keepa_layout.addRow("Max Retries:", self.max_retries)
        
        self.rate_limit_delay = QDoubleSpinBox()
        self.rate_limit_delay.setRange(0.1, 10.0)
        self.rate_limit_delay.setSuffix(" seconds")
        self.rate_limit_delay.setSingleStep(0.1)
        keepa_layout.addRow("Rate Limit Delay:", self.rate_limit_delay)
        
        keepa_group.setLayout(keepa_layout)
        layout.addWidget(keepa_group)
        
        # API Status Info
        status_group = QGroupBox("API Status")
        status_layout = QVBoxLayout()
        
        self.api_status_label = QLabel("Click 'Test APIs' to check API connectivity")
        self.api_status_label.setStyleSheet("color: #666; font-style: italic;")
        status_layout.addWidget(self.api_status_label)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        layout.addStretch()
        return tab
    
    def create_analysis_tab(self) -> QWidget:
        """Create analysis settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Profitability Settings
        profit_group = QGroupBox("Profitability Analysis")
        profit_layout = QFormLayout()
        
        self.min_roi_threshold = QDoubleSpinBox()
        self.min_roi_threshold.setRange(0, 100)
        self.min_roi_threshold.setSuffix("%")
        profit_layout.addRow("Minimum ROI Threshold:", self.min_roi_threshold)
        
        self.profit_margin_threshold = QDoubleSpinBox()
        self.profit_margin_threshold.setRange(0, 100)
        self.profit_margin_threshold.setSuffix("%")
        profit_layout.addRow("Profit Margin Threshold:", self.profit_margin_threshold)
        
        self.vat_rate = QDoubleSpinBox()
        self.vat_rate.setRange(0, 1)
        self.vat_rate.setSingleStep(0.01)
        self.vat_rate.setDecimals(2)
        profit_layout.addRow("VAT Rate:", self.vat_rate)
        
        profit_group.setLayout(profit_layout)
        layout.addWidget(profit_group)
        
        # Product Settings
        product_group = QGroupBox("Product Analysis")
        product_layout = QFormLayout()
        
        self.default_weight_kg = QDoubleSpinBox()
        self.default_weight_kg.setRange(0.01, 100)
        self.default_weight_kg.setSuffix(" kg")
        self.default_weight_kg.setSingleStep(0.1)
        product_layout.addRow("Default Weight:", self.default_weight_kg)
        
        self.default_category = QLineEdit()
        self.default_category.setPlaceholderText("default")
        product_layout.addRow("Default Category:", self.default_category)
        
        self.currency_symbol = QLineEdit()
        self.currency_symbol.setMaxLength(3)
        product_layout.addRow("Currency Symbol:", self.currency_symbol)
        
        product_group.setLayout(product_layout)
        layout.addWidget(product_group)
        
        layout.addStretch()
        return tab
    
    def create_qogita_tab(self) -> QWidget:
        """Create Qogita settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Qogita Account Settings
        account_group = QGroupBox("Qogita Account")
        account_layout = QFormLayout()
        
        self.qogita_email = QLineEdit()
        self.qogita_email.setPlaceholderText("your-email@domain.com")
        account_layout.addRow("Email:", self.qogita_email)
        
        self.qogita_password = QLineEdit()
        self.qogita_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.qogita_password.setPlaceholderText("Your Qogita password")
        account_layout.addRow("Password:", self.qogita_password)
        
        account_group.setLayout(account_layout)
        layout.addWidget(account_group)
        
        # Qogita API Settings
        api_group = QGroupBox("Qogita API Settings")
        api_layout = QFormLayout()
        
        self.qogita_rate_limit = QDoubleSpinBox()
        self.qogita_rate_limit.setRange(0.1, 60.0)
        self.qogita_rate_limit.setSuffix(" seconds")
        self.qogita_rate_limit.setSingleStep(0.1)
        api_layout.addRow("Rate Limit Delay:", self.qogita_rate_limit)
        
        self.qogita_timeout = QSpinBox()
        self.qogita_timeout.setRange(10, 300)
        self.qogita_timeout.setSuffix(" seconds")
        api_layout.addRow("Request Timeout:", self.qogita_timeout)
        
        api_group.setLayout(api_layout)
        layout.addWidget(api_group)
        
        # Info
        info_label = QLabel("ℹ️ Qogita credentials are used for accessing wholesale product data")
        info_label.setStyleSheet("color: #666; font-style: italic; margin-top: 10px;")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        layout.addStretch()
        return tab
    
    def create_ui_tab(self) -> QWidget:
        """Create UI settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Window Settings
        window_group = QGroupBox("Window Settings")
        window_layout = QFormLayout()
        
        self.window_width = QSpinBox()
        self.window_width.setRange(600, 2000)
        self.window_width.setSuffix(" px")
        window_layout.addRow("Default Width:", self.window_width)
        
        self.window_height = QSpinBox()
        self.window_height.setRange(400, 1500)
        self.window_height.setSuffix(" px")
        window_layout.addRow("Default Height:", self.window_height)
        
        window_group.setLayout(window_layout)
        layout.addWidget(window_group)
        
        # Display Settings
        display_group = QGroupBox("Display Settings")
        display_layout = QFormLayout()
        
        self.decimal_places = QSpinBox()
        self.decimal_places.setRange(0, 4)
        display_layout.addRow("Decimal Places:", self.decimal_places)
        
        self.show_tooltips = QCheckBox("Show helpful tooltips")
        display_layout.addRow("Tooltips:", self.show_tooltips)
        
        self.show_advanced_options = QCheckBox("Show advanced options by default")
        display_layout.addRow("Advanced Options:", self.show_advanced_options)
        
        display_group.setLayout(display_layout)
        layout.addWidget(display_group)
        
        layout.addStretch()
        return tab
    
    def load_config(self) -> dict:
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
        
        # Return default config
        return {
            "keepa_api_key": "",
            "min_roi_threshold": 15.0,
            "amazon_marketplace": "france",
            "default_weight_kg": 0.5,
            "default_category": "default",
            "currency_symbol": "€",
            "vat_rate": 0.2,
            "ui_settings": {
                "window_width": 800,
                "window_height": 600,
                "decimal_places": 2,
                "show_tooltips": True,
                "show_advanced_options": False
            },
            "api_settings": {
                "request_timeout": 30,
                "max_retries": 3,
                "rate_limit_delay": 1.0
            },
            "qogita_settings": {
                "email": "",
                "password": "",
                "rate_limit_delay": 1.0,
                "timeout": 60
            }
        }
    
    def load_settings(self):
        """Load settings into the UI"""
        # API Settings
        self.keepa_api_key.setText(self.config.get('keepa_api_key', ''))
        self.amazon_marketplace.setCurrentText(self.config.get('amazon_marketplace', 'france'))
        
        api_settings = self.config.get('api_settings', {})
        self.request_timeout.setValue(api_settings.get('request_timeout', 30))
        self.max_retries.setValue(api_settings.get('max_retries', 3))
        self.rate_limit_delay.setValue(api_settings.get('rate_limit_delay', 1.0))
        
        # Analysis Settings
        self.min_roi_threshold.setValue(self.config.get('min_roi_threshold', 15.0))
        self.profit_margin_threshold.setValue(self.config.get('profit_margin_threshold', 10.0))
        self.vat_rate.setValue(self.config.get('vat_rate', 0.2))
        self.default_weight_kg.setValue(self.config.get('default_weight_kg', 0.5))
        self.default_category.setText(self.config.get('default_category', 'default'))
        self.currency_symbol.setText(self.config.get('currency_symbol', '€'))
        
        # Qogita Settings
        qogita_settings = self.config.get('qogita_settings', {})
        self.qogita_email.setText(qogita_settings.get('email', ''))
        self.qogita_password.setText(qogita_settings.get('password', ''))
        self.qogita_rate_limit.setValue(qogita_settings.get('rate_limit_delay', 1.0))
        self.qogita_timeout.setValue(qogita_settings.get('timeout', 60))
        
        # UI Settings
        ui_settings = self.config.get('ui_settings', {})
        self.window_width.setValue(ui_settings.get('window_width', 800))
        self.window_height.setValue(ui_settings.get('window_height', 600))
        self.decimal_places.setValue(ui_settings.get('decimal_places', 2))
        self.show_tooltips.setChecked(ui_settings.get('show_tooltips', True))
        self.show_advanced_options.setChecked(ui_settings.get('show_advanced_options', False))
    
    def save_settings(self):
        """Save settings to configuration file"""
        try:
            # Update config dictionary
            self.config['keepa_api_key'] = self.keepa_api_key.text()
            self.config['amazon_marketplace'] = self.amazon_marketplace.currentText()
            self.config['min_roi_threshold'] = self.min_roi_threshold.value()
            self.config['profit_margin_threshold'] = self.profit_margin_threshold.value()
            self.config['vat_rate'] = self.vat_rate.value()
            self.config['default_weight_kg'] = self.default_weight_kg.value()
            self.config['default_category'] = self.default_category.text()
            self.config['currency_symbol'] = self.currency_symbol.text()
            
            # API Settings
            self.config['api_settings'] = {
                'request_timeout': self.request_timeout.value(),
                'max_retries': self.max_retries.value(),
                'rate_limit_delay': self.rate_limit_delay.value()
            }
            
            # Qogita Settings
            self.config['qogita_settings'] = {
                'email': self.qogita_email.text(),
                'password': self.qogita_password.text(),
                'rate_limit_delay': self.qogita_rate_limit.value(),
                'timeout': self.qogita_timeout.value()
            }
            
            # UI Settings
            self.config['ui_settings'] = {
                'window_width': self.window_width.value(),
                'window_height': self.window_height.value(),
                'decimal_places': self.decimal_places.value(),
                'show_tooltips': self.show_tooltips.isChecked(),
                'show_advanced_options': self.show_advanced_options.isChecked()
            }
            
            # Save to file
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            
            QMessageBox.information(self, "Settings Saved", 
                                   "Settings have been saved successfully!\n\n"
                                   "Some changes may require restarting the application.")
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error Saving Settings", 
                               f"Failed to save settings:\n{str(e)}")
    
    def test_apis(self):
        """Test API connectivity"""
        self.api_status_label.setText("🔄 Testing APIs...")
        self.test_btn.setEnabled(False)
        
        # Simple test - just check if API key is provided
        keepa_key = self.keepa_api_key.text()
        qogita_email = self.qogita_email.text()
        
        status_parts = []
        
        if keepa_key:
            status_parts.append("✅ Keepa API key provided")
        else:
            status_parts.append("❌ Keepa API key missing")
        
        if qogita_email:
            status_parts.append("✅ Qogita email provided")
        else:
            status_parts.append("❌ Qogita email missing")
        
        self.api_status_label.setText("\n".join(status_parts))
        self.test_btn.setEnabled(True)
