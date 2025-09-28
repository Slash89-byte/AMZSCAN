"""
Configuration dialog for Amazon Profitability Analyzer
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget, 
    QFormLayout, QLineEdit, QSpinBox, QDoubleSpinBox, QCheckBox,
    QComboBox, QGroupBox, QPushButton, QMessageBox, QLabel,
    QSlider, QTextEdit, QFileDialog
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QIcon
from utils.config import Config

class ConfigurationDialog(QDialog):
    """Configuration dialog for user settings"""
    
    # Signal emitted when configuration is saved
    configuration_saved = pyqtSignal()
    
    def __init__(self, parent=None, config: Config = None):
        super().__init__(parent)
        self.config = config or Config()
        self.setWindowTitle("Configuration - Amazon Profitability Analyzer")
        self.setModal(True)
        self.resize(600, 500)
        self.setup_ui()
        self.load_current_settings()
    
    def setup_ui(self):
        """Set up the user interface"""
        layout = QVBoxLayout()
        
        # Create tab widget for different configuration sections
        self.tab_widget = QTabWidget()
        
        # Create tabs
        self.create_general_tab()
        self.create_vat_tax_tab()
        self.create_analysis_tab()
        self.create_business_model_tab()
        self.create_advanced_tab()
        
        layout.addWidget(self.tab_widget)
        
        # Add buttons
        button_layout = self.create_button_layout()
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def create_general_tab(self):
        """Create general settings tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # API Configuration Group
        api_group = QGroupBox("API Configuration")
        api_layout = QFormLayout()
        
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_edit.setPlaceholderText("Enter your Keepa API key")
        api_layout.addRow("Keepa API Key:", self.api_key_edit)
        
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(10, 300)
        self.timeout_spin.setSuffix(" seconds")
        api_layout.addRow("Request Timeout:", self.timeout_spin)
        
        api_group.setLayout(api_layout)
        layout.addWidget(api_group)
        
        # Marketplace Configuration Group
        marketplace_group = QGroupBox("Marketplace Settings")
        marketplace_layout = QFormLayout()
        
        self.marketplace_combo = QComboBox()
        self.marketplace_combo.addItems(["france", "germany", "italy", "uk", "us"])
        marketplace_layout.addRow("Amazon Marketplace:", self.marketplace_combo)
        
        self.currency_edit = QLineEdit()
        self.currency_edit.setMaxLength(3)
        marketplace_layout.addRow("Currency Symbol:", self.currency_edit)
        
        marketplace_group.setLayout(marketplace_layout)
        layout.addWidget(marketplace_group)
        
        # Profitability Thresholds Group
        thresholds_group = QGroupBox("Profitability Thresholds")
        thresholds_layout = QFormLayout()
        
        self.roi_threshold_spin = QDoubleSpinBox()
        self.roi_threshold_spin.setRange(0.0, 100.0)
        self.roi_threshold_spin.setSuffix("%")
        self.roi_threshold_spin.setDecimals(1)
        thresholds_layout.addRow("Minimum ROI Threshold:", self.roi_threshold_spin)
        
        self.margin_threshold_spin = QDoubleSpinBox()
        self.margin_threshold_spin.setRange(0.0, 50.0)
        self.margin_threshold_spin.setSuffix("%")
        self.margin_threshold_spin.setDecimals(1)
        thresholds_layout.addRow("Profit Margin Threshold:", self.margin_threshold_spin)
        
        thresholds_group.setLayout(thresholds_layout)
        layout.addWidget(thresholds_group)
        
        layout.addStretch()
        tab.setLayout(layout)
        self.tab_widget.addTab(tab, "General")
    
    def create_vat_tax_tab(self):
        """Create VAT and tax settings tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # VAT Configuration Group
        vat_group = QGroupBox("VAT Configuration")
        vat_layout = QFormLayout()
        
        self.vat_rate_spin = QDoubleSpinBox()
        self.vat_rate_spin.setRange(0.0, 0.5)  # 0% to 50%
        self.vat_rate_spin.setSuffix("%")
        self.vat_rate_spin.setDecimals(2)
        self.vat_rate_spin.setValue(20.0)  # Default 20%
        vat_layout.addRow("VAT Rate:", self.vat_rate_spin)
        
        self.vat_on_cost_checkbox = QCheckBox()
        self.vat_on_cost_checkbox.setToolTip(
            "Apply VAT on your cost prices (e.g., if you pay VAT when purchasing products)"
        )
        vat_layout.addRow("Apply VAT on Cost Price:", self.vat_on_cost_checkbox)
        
        self.vat_on_sale_checkbox = QCheckBox()
        self.vat_on_sale_checkbox.setToolTip(
            "Apply VAT calculations on Amazon selling prices (e.g., to exclude VAT for fee calculations)"
        )
        vat_layout.addRow("Apply VAT on Selling Price:", self.vat_on_sale_checkbox)
        
        self.amazon_prices_include_vat_checkbox = QCheckBox()
        self.amazon_prices_include_vat_checkbox.setChecked(True)
        self.amazon_prices_include_vat_checkbox.setToolTip(
            "In EU, Amazon prices typically include VAT. Uncheck if working with VAT-exclusive prices."
        )
        vat_layout.addRow("Amazon Prices Include VAT:", self.amazon_prices_include_vat_checkbox)
        
        vat_group.setLayout(vat_layout)
        layout.addWidget(vat_group)
        
        # VAT Explanation
        explanation_group = QGroupBox("VAT Scenarios Explanation")
        explanation_layout = QVBoxLayout()
        
        explanation_text = QTextEdit()
        explanation_text.setMaximumHeight(120)
        explanation_text.setReadOnly(True)
        explanation_text.setPlainText(
            "VAT Scenarios:\n"
            "• Apply VAT on Cost: Your purchase costs include VAT (typical for retail arbitrage)\n"
            "• Apply VAT on Sale: Amazon selling prices need VAT adjustments (for fee calculations)\n"
            "• Amazon Prices Include VAT: Standard for EU marketplaces\n\n"
            "Example: If you buy for €10 + 20% VAT = €12 cost, enable 'Apply VAT on Cost' for accurate ROI."
        )
        explanation_layout.addWidget(explanation_text)
        explanation_group.setLayout(explanation_layout)
        layout.addWidget(explanation_group)
        
        layout.addStretch()
        tab.setLayout(layout)
        self.tab_widget.addTab(tab, "VAT & Tax")
    
    def create_analysis_tab(self):
        """Create product analysis settings tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Analysis Criteria Group
        criteria_group = QGroupBox("Analysis Criteria")
        criteria_layout = QFormLayout()
        
        self.consider_sales_rank_checkbox = QCheckBox()
        criteria_layout.addRow("Consider Sales Rank:", self.consider_sales_rank_checkbox)
        
        self.max_sales_rank_spin = QSpinBox()
        self.max_sales_rank_spin.setRange(1000, 10000000)
        self.max_sales_rank_spin.setValue(100000)
        criteria_layout.addRow("Max Acceptable Sales Rank:", self.max_sales_rank_spin)
        
        self.min_reviews_spin = QSpinBox()
        self.min_reviews_spin.setRange(0, 10000)
        criteria_layout.addRow("Minimum Review Count:", self.min_reviews_spin)
        
        self.min_rating_spin = QDoubleSpinBox()
        self.min_rating_spin.setRange(0.0, 5.0)
        self.min_rating_spin.setDecimals(1)
        self.min_rating_spin.setSingleStep(0.1)
        criteria_layout.addRow("Minimum Rating:", self.min_rating_spin)
        
        self.check_buybox_checkbox = QCheckBox()
        self.check_buybox_checkbox.setChecked(True)
        criteria_layout.addRow("Check Buy Box Eligibility:", self.check_buybox_checkbox)
        
        criteria_group.setLayout(criteria_layout)
        layout.addWidget(criteria_group)
        
        # Product Defaults Group
        defaults_group = QGroupBox("Product Defaults")
        defaults_layout = QFormLayout()
        
        self.default_weight_spin = QDoubleSpinBox()
        self.default_weight_spin.setRange(0.01, 100.0)
        self.default_weight_spin.setDecimals(3)
        self.default_weight_spin.setSuffix(" kg")
        defaults_layout.addRow("Default Product Weight:", self.default_weight_spin)
        
        self.default_category_combo = QComboBox()
        self.default_category_combo.addItems([
            "default", "electronics", "beauty", "books", "clothing", 
            "home_garden", "sports", "toys"
        ])
        defaults_layout.addRow("Default Category:", self.default_category_combo)
        
        defaults_group.setLayout(defaults_layout)
        layout.addWidget(defaults_group)
        
        layout.addStretch()
        tab.setLayout(layout)
        self.tab_widget.addTab(tab, "Analysis")
    
    def create_business_model_tab(self):
        """Create business model settings tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Business Model Group
        model_group = QGroupBox("Business Model")
        model_layout = QFormLayout()
        
        self.business_model_combo = QComboBox()
        self.business_model_combo.addItems([
            "retail_arbitrage", "wholesale", "private_label"
        ])
        model_layout.addRow("Business Model Type:", self.business_model_combo)
        
        model_group.setLayout(model_layout)
        layout.addWidget(model_group)
        
        # Additional Costs Group
        costs_group = QGroupBox("Additional Costs")
        costs_layout = QFormLayout()
        
        self.additional_cost_percentage_spin = QDoubleSpinBox()
        self.additional_cost_percentage_spin.setRange(0.0, 100.0)
        self.additional_cost_percentage_spin.setSuffix("%")
        self.additional_cost_percentage_spin.setDecimals(1)
        costs_layout.addRow("Additional Cost Percentage:", self.additional_cost_percentage_spin)
        
        self.shipping_cost_spin = QDoubleSpinBox()
        self.shipping_cost_spin.setRange(0.0, 1000.0)
        self.shipping_cost_spin.setPrefix("€")
        self.shipping_cost_spin.setDecimals(2)
        costs_layout.addRow("Shipping Cost per Unit:", self.shipping_cost_spin)
        
        self.prep_cost_spin = QDoubleSpinBox()
        self.prep_cost_spin.setRange(0.0, 100.0)
        self.prep_cost_spin.setPrefix("€")
        self.prep_cost_spin.setDecimals(2)
        costs_layout.addRow("Prep Cost per Unit:", self.prep_cost_spin)
        
        costs_group.setLayout(costs_layout)
        layout.addWidget(costs_group)
        
        layout.addStretch()
        tab.setLayout(layout)
        self.tab_widget.addTab(tab, "Business Model")
    
    def create_advanced_tab(self):
        """Create advanced settings tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # UI Settings Group
        ui_group = QGroupBox("User Interface")
        ui_layout = QFormLayout()
        
        self.decimal_places_spin = QSpinBox()
        self.decimal_places_spin.setRange(0, 6)
        self.decimal_places_spin.setValue(2)
        ui_layout.addRow("Decimal Places:", self.decimal_places_spin)
        
        self.show_advanced_checkbox = QCheckBox()
        ui_layout.addRow("Show Advanced Options:", self.show_advanced_checkbox)
        
        self.show_tooltips_checkbox = QCheckBox()
        self.show_tooltips_checkbox.setChecked(True)
        ui_layout.addRow("Show Tooltips:", self.show_tooltips_checkbox)
        
        ui_group.setLayout(ui_layout)
        layout.addWidget(ui_group)
        
        # Cache Settings Group
        cache_group = QGroupBox("Cache Settings")
        cache_layout = QFormLayout()
        
        self.cache_duration_spin = QSpinBox()
        self.cache_duration_spin.setRange(1, 1440)  # 1 minute to 24 hours
        self.cache_duration_spin.setSuffix(" minutes")
        self.cache_duration_spin.setValue(15)
        cache_layout.addRow("Cache Duration:", self.cache_duration_spin)
        
        cache_group.setLayout(cache_layout)
        layout.addWidget(cache_group)
        
        # Import/Export Group
        import_export_group = QGroupBox("Import/Export Configuration")
        import_export_layout = QHBoxLayout()
        
        export_button = QPushButton("Export Config")
        export_button.clicked.connect(self.export_configuration)
        import_export_layout.addWidget(export_button)
        
        import_button = QPushButton("Import Config")
        import_button.clicked.connect(self.import_configuration)
        import_export_layout.addWidget(import_button)
        
        import_export_group.setLayout(import_export_layout)
        layout.addWidget(import_export_group)
        
        layout.addStretch()
        tab.setLayout(layout)
        self.tab_widget.addTab(tab, "Advanced")
    
    def create_button_layout(self):
        """Create the button layout"""
        layout = QHBoxLayout()
        layout.addStretch()
        
        # Reset to defaults button
        reset_button = QPushButton("Reset to Defaults")
        reset_button.clicked.connect(self.reset_to_defaults)
        layout.addWidget(reset_button)
        
        # Cancel button
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        layout.addWidget(cancel_button)
        
        # Save button
        save_button = QPushButton("Save & Apply")
        save_button.setDefault(True)
        save_button.clicked.connect(self.save_configuration)
        layout.addWidget(save_button)
        
        return layout
    
    def load_current_settings(self):
        """Load current configuration into UI elements"""
        # General tab
        self.api_key_edit.setText(self.config.get_keepa_api_key())
        self.timeout_spin.setValue(self.config.get('api_settings.request_timeout', 30))
        self.marketplace_combo.setCurrentText(self.config.get('amazon_marketplace', 'france'))
        self.currency_edit.setText(self.config.get('currency_symbol', '€'))
        self.roi_threshold_spin.setValue(self.config.get('min_roi_threshold', 15.0))
        self.margin_threshold_spin.setValue(self.config.get('profit_margin_threshold', 10.0))
        
        # VAT tab
        vat_rate = self.config.get_vat_rate() * 100  # Convert to percentage
        self.vat_rate_spin.setValue(vat_rate)
        self.vat_on_cost_checkbox.setChecked(self.config.get_apply_vat_on_cost())
        self.vat_on_sale_checkbox.setChecked(self.config.get_apply_vat_on_sale())
        self.amazon_prices_include_vat_checkbox.setChecked(self.config.get_vat_included_in_amazon_prices())
        
        # Analysis tab
        analysis_settings = self.config.get_analysis_settings()
        self.consider_sales_rank_checkbox.setChecked(analysis_settings['consider_sales_rank'])
        self.max_sales_rank_spin.setValue(analysis_settings['max_acceptable_sales_rank'])
        self.min_reviews_spin.setValue(analysis_settings['min_review_count'])
        self.min_rating_spin.setValue(analysis_settings['min_rating'])
        self.check_buybox_checkbox.setChecked(analysis_settings['check_buy_box_eligibility'])
        
        self.default_weight_spin.setValue(self.config.get('default_weight_kg', 0.5))
        self.default_category_combo.setCurrentText(self.config.get('default_category', 'default'))
        
        # Business model tab
        self.business_model_combo.setCurrentText(self.config.get_business_model_type())
        additional_costs = self.config.get_additional_costs()
        self.additional_cost_percentage_spin.setValue(additional_costs['percentage'])
        self.shipping_cost_spin.setValue(additional_costs['shipping_per_unit'])
        self.prep_cost_spin.setValue(additional_costs['prep_per_unit'])
        
        # Advanced tab
        self.decimal_places_spin.setValue(self.config.get('ui_settings.decimal_places', 2))
        self.show_advanced_checkbox.setChecked(self.config.get('ui_settings.show_advanced_options', False))
        self.show_tooltips_checkbox.setChecked(self.config.get('ui_settings.show_tooltips', True))
        self.cache_duration_spin.setValue(self.config.get('api_settings.cache_duration_minutes', 15))
    
    def save_configuration(self):
        """Save configuration from UI elements"""
        try:
            # General settings
            self.config.set_keepa_api_key(self.api_key_edit.text())
            self.config.set('api_settings.request_timeout', self.timeout_spin.value())
            self.config.set('amazon_marketplace', self.marketplace_combo.currentText())
            self.config.set('currency_symbol', self.currency_edit.text())
            self.config.set('min_roi_threshold', self.roi_threshold_spin.value())
            self.config.set('profit_margin_threshold', self.margin_threshold_spin.value())
            
            # VAT settings
            vat_rate = self.vat_rate_spin.value() / 100  # Convert from percentage
            self.config.set_vat_rate(vat_rate)
            self.config.set_apply_vat_on_cost(self.vat_on_cost_checkbox.isChecked())
            self.config.set_apply_vat_on_sale(self.vat_on_sale_checkbox.isChecked())
            self.config.set_vat_included_in_amazon_prices(self.amazon_prices_include_vat_checkbox.isChecked())
            
            # Analysis settings
            self.config.set('analysis_settings.consider_sales_rank', self.consider_sales_rank_checkbox.isChecked())
            self.config.set('analysis_settings.max_acceptable_sales_rank', self.max_sales_rank_spin.value())
            self.config.set('analysis_settings.min_review_count', self.min_reviews_spin.value())
            self.config.set('analysis_settings.min_rating', self.min_rating_spin.value())
            self.config.set('analysis_settings.check_buy_box_eligibility', self.check_buybox_checkbox.isChecked())
            
            self.config.set('default_weight_kg', self.default_weight_spin.value())
            self.config.set('default_category', self.default_category_combo.currentText())
            
            # Business model settings
            self.config.set_business_model_type(self.business_model_combo.currentText())
            self.config.set('business_model.additional_cost_percentage', self.additional_cost_percentage_spin.value())
            self.config.set('business_model.shipping_cost_per_unit', self.shipping_cost_spin.value())
            self.config.set('business_model.prep_cost_per_unit', self.prep_cost_spin.value())
            
            # Advanced settings
            self.config.set('ui_settings.decimal_places', self.decimal_places_spin.value())
            self.config.set('ui_settings.show_advanced_options', self.show_advanced_checkbox.isChecked())
            self.config.set('ui_settings.show_tooltips', self.show_tooltips_checkbox.isChecked())
            self.config.set('api_settings.cache_duration_minutes', self.cache_duration_spin.value())
            
            # Save to file
            self.config.save_config()
            
            # Emit signal and close
            self.configuration_saved.emit()
            QMessageBox.information(self, "Success", "Configuration saved successfully!")
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save configuration: {str(e)}")
    
    def reset_to_defaults(self):
        """Reset configuration to default values"""
        result = QMessageBox.question(
            self, "Reset Configuration",
            "Are you sure you want to reset all settings to their default values?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if result == QMessageBox.StandardButton.Yes:
            # Reset config to defaults
            self.config = Config()  # Create fresh config with defaults
            self.load_current_settings()
    
    def export_configuration(self):
        """Export configuration to file"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Configuration", "config_export.json", "JSON Files (*.json)"
        )
        
        if filename:
            if self.config.export_config(filename):
                QMessageBox.information(self, "Success", "Configuration exported successfully!")
            else:
                QMessageBox.critical(self, "Error", "Failed to export configuration!")
    
    def import_configuration(self):
        """Import configuration from file"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Import Configuration", "", "JSON Files (*.json)"
        )
        
        if filename:
            if self.config.import_config(filename):
                self.load_current_settings()
                QMessageBox.information(self, "Success", "Configuration imported successfully!")
            else:
                QMessageBox.critical(self, "Error", "Failed to import configuration!")
