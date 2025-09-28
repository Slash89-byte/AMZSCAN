"""
Configuration management for the Amazon Profitability Analyzer
"""

import json
import os
from typing import Any, Dict, Optional

class Config:
    """Configuration manager for storing API keys, settings, and user preferences"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config_path = self._get_config_path()
        self.settings = self._load_config()
    
    def _get_config_path(self) -> str:
        """Get the full path to the config file"""
        # Store config in the same directory as the application
        app_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(os.path.dirname(app_dir), self.config_file)
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default config"""
        default_config = {
            # API Configuration
            'api_settings': {
                'keepa_api_key': '',
                'default_domain': 'france',
                'amazon_domain': 4,  # France domain
                'currency_symbol': '€',
                'request_timeout': 30,
                'max_retries': 3,
                'rate_limit_delay': 1.0,
                'cache_duration_minutes': 15,
            },
            
            # VAT Configuration
            'vat_settings': {
                'vat_rate': 20.0,  # 20% for France
                'apply_vat_on_cost': True,  # Apply VAT on cost price
                'apply_vat_on_sale': False,  # Apply VAT on selling price
                'vat_included_in_amazon_prices': True,  # Amazon prices include VAT (EU standard)
            },
            
            # Analysis Settings
            'analysis_settings': {
                'min_roi_threshold': 15.0,
                'max_cost_price': 500.0,
                'profit_margin_threshold': 10.0,
                'consider_sales_rank': True,
                'max_acceptable_sales_rank': 100000,
                'min_review_count': 0,
                'min_rating': 0.0,
                'check_buy_box_eligibility': True,
            },
            
            # Business Model Settings
            'business_model_settings': {
                'business_model': 'retail_arbitrage',
                'risk_tolerance': 'medium',
                'additional_cost_percentage': 0.0,
                'shipping_cost_per_unit': 0.0,
                'prep_cost_per_unit': 0.0,
            },
            
            # Advanced Settings
            'advanced_settings': {
                'enable_debug_mode': False,
                'auto_save_results': True,
                'cache_keepa_data': True,
                'enable_logging': False,
                'log_level': 'INFO',
            },
            
            # UI Settings
            'ui_settings': {
                'window_width': 900,
                'window_height': 700,
                'theme': 'default',
                'show_advanced_options': False,
                'decimal_places': 2,
                'show_tooltips': True,
            },
            
            # Legacy flat keys for backward compatibility
            'keepa_api_key': '',
            'min_roi_threshold': 15.0,
            'amazon_marketplace': 'france',
            'default_weight_kg': 0.5,
            'default_category': 'default',
        }
        
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                
                # Merge with defaults to ensure all keys exist
                for key, value in default_config.items():
                    if key not in loaded_config:
                        loaded_config[key] = value
                    elif isinstance(value, dict) and isinstance(loaded_config[key], dict):
                        # Merge nested dictionaries
                        for nested_key, nested_value in value.items():
                            if nested_key not in loaded_config[key]:
                                loaded_config[key][nested_key] = nested_value
                
                return loaded_config
            else:
                return default_config
                
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading config file: {e}")
            return default_config
    
    def save_config(self) -> bool:
        """Save current configuration to file"""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
            
            return True
            
        except (IOError, OSError) as e:
            print(f"Error saving config file: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value"""
        keys = key.split('.')
        value = self.settings
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value"""
        keys = key.split('.')
        current = self.settings
        
        # Navigate to the parent dictionary
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        # Set the final value
        current[keys[-1]] = value
    
    def is_configured(self) -> bool:
        """Check if the application is properly configured"""
        return bool(self.get('keepa_api_key'))
    
    def get_keepa_api_key(self) -> str:
        """Get the Keepa API key"""
        return self.get('keepa_api_key', '')
    
    def set_keepa_api_key(self, api_key: str) -> None:
        """Set the Keepa API key"""
        self.set('keepa_api_key', api_key)
        self.save_config()
    
    def get_min_roi_threshold(self) -> float:
        """Get the minimum ROI threshold for profitability"""
        return self.get('min_roi_threshold', 15.0)
    
    def set_min_roi_threshold(self, threshold: float) -> None:
        """Set the minimum ROI threshold"""
        self.set('min_roi_threshold', threshold)
        self.save_config()
    
    def get_marketplace_settings(self) -> Dict[str, Any]:
        """Get marketplace-specific settings"""
        marketplace = self.get('amazon_marketplace', 'france')
        
        marketplace_configs = {
            'france': {
                'domain_id': 4,  # Corrected: France is domain 4, not 8
                'currency': 'EUR',
                'currency_symbol': '€',
                'vat_rate': 0.20,
                'base_url': 'amazon.fr'
            },
            'germany': {
                'domain_id': 3,
                'currency': 'EUR',
                'currency_symbol': '€',
                'vat_rate': 0.19,
                'base_url': 'amazon.de'
            },
            'italy': {
                'domain_id': 8,
                'currency': 'EUR',
                'currency_symbol': '€',
                'vat_rate': 0.22,
                'base_url': 'amazon.it'
            },
            'uk': {
                'domain_id': 2,
                'currency': 'GBP',
                'currency_symbol': '£',
                'vat_rate': 0.20,
                'base_url': 'amazon.co.uk'
            },
            'us': {
                'domain_id': 1,
                'currency': 'USD',
                'currency_symbol': '$',
                'vat_rate': 0.0,  # Sales tax varies by state
                'base_url': 'amazon.com'
            }
        }
        
        return marketplace_configs.get(marketplace, marketplace_configs['france'])
    
    def update_ui_settings(self, width: int, height: int) -> None:
        """Update UI window size settings"""
        self.set('ui_settings.window_width', width)
        self.set('ui_settings.window_height', height)
        self.save_config()
    
    def reset_to_defaults(self) -> None:
        """Reset configuration to default values"""
        self.settings = self._load_config()
        # Clear the existing config file
        if os.path.exists(self.config_path):
            os.remove(self.config_path)
        self.save_config()
    
    def export_config(self, export_path: str) -> bool:
        """Export configuration to a different file"""
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
            return True
        except (IOError, OSError):
            return False
    
    def import_config(self, import_path: str) -> bool:
        """Import configuration from a file"""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)
            
            self.settings = imported_config
            self.save_config()
            return True
            
        except (json.JSONDecodeError, IOError):
            return False
    
    # VAT Configuration Helper Methods
    def get_vat_rate(self) -> float:
        """Get the current VAT rate"""
        return self.get('vat_settings.vat_rate', 0.20)
    
    def set_vat_rate(self, rate: float) -> None:
        """Set the VAT rate"""
        self.set('vat_settings.vat_rate', max(0.0, min(1.0, rate)))
    
    def get_apply_vat_on_cost(self) -> bool:
        """Check if VAT should be applied on cost prices"""
        return self.get('vat_settings.apply_vat_on_cost', False)
    
    def set_apply_vat_on_cost(self, apply: bool) -> None:
        """Set whether to apply VAT on cost prices"""
        self.set('vat_settings.apply_vat_on_cost', apply)
    
    def get_apply_vat_on_sale(self) -> bool:
        """Check if VAT should be applied on selling prices"""
        return self.get('vat_settings.apply_vat_on_sale', False)
    
    def set_apply_vat_on_sale(self, apply: bool) -> None:
        """Set whether to apply VAT on selling prices"""
        self.set('vat_settings.apply_vat_on_sale', apply)
    
    def get_vat_included_in_amazon_prices(self) -> bool:
        """Check if Amazon prices include VAT"""
        return self.get('vat_settings.vat_included_in_amazon_prices', True)
    
    def set_vat_included_in_amazon_prices(self, included: bool) -> None:
        """Set whether Amazon prices include VAT"""
        self.set('vat_settings.vat_included_in_amazon_prices', included)
    
    # Business Model Helper Methods
    def get_business_model_type(self) -> str:
        """Get the current business model type"""
        return self.get('business_model.model_type', 'retail_arbitrage')
    
    def set_business_model_type(self, model_type: str) -> None:
        """Set the business model type"""
        valid_types = ['retail_arbitrage', 'wholesale', 'private_label']
        if model_type in valid_types:
            self.set('business_model.model_type', model_type)
    
    def get_additional_costs(self) -> dict:
        """Get all additional cost settings"""
        return {
            'percentage': self.get('business_model.additional_cost_percentage', 0.0),
            'shipping_per_unit': self.get('business_model.shipping_cost_per_unit', 0.0),
            'prep_per_unit': self.get('business_model.prep_cost_per_unit', 0.0),
        }
    
    # Analysis Settings Helper Methods
    def get_analysis_settings(self) -> dict:
        """Get all analysis settings"""
        return {
            'consider_sales_rank': self.get('analysis_settings.consider_sales_rank', True),
            'max_acceptable_sales_rank': self.get('analysis_settings.max_acceptable_sales_rank', 100000),
            'min_review_count': self.get('analysis_settings.min_review_count', 0),
            'min_rating': self.get('analysis_settings.min_rating', 0.0),
            'check_buy_box_eligibility': self.get('analysis_settings.check_buy_box_eligibility', True),
        }
    
    # Validation Methods
    def validate_vat_rate(self, vat_rate: float) -> bool:
        """Validate VAT rate is within acceptable range (0-100)"""
        return 0.0 <= vat_rate <= 100.0
    
    def validate_roi_threshold(self, roi_threshold: float) -> bool:
        """Validate ROI threshold is within acceptable range (0-1000)"""
        return 0.0 <= roi_threshold <= 1000.0
    
    def validate_max_cost_price(self, max_cost: float) -> bool:
        """Validate maximum cost price is within acceptable range (1-10000)"""
        return 1.0 <= max_cost <= 10000.0
    
    def validate_api_key(self, api_key: str) -> bool:
        """Validate API key format (basic check)"""
        return isinstance(api_key, str) and len(api_key.strip()) > 0
    
    def validate_domain(self, domain: str) -> bool:
        """Validate domain is supported"""
        valid_domains = ['france', 'germany', 'italy', 'spain', 'uk', 'usa']
        return domain.lower() in valid_domains
    
    # Enhanced Helper Methods with Validation
    def set_vat_rate(self, vat_rate: float) -> None:
        """Set VAT rate with validation"""
        if not self.validate_vat_rate(vat_rate):
            raise ValueError(f"VAT rate must be between 0 and 100, got {vat_rate}")
        self.set('vat_settings.vat_rate', vat_rate)
    
    def set_min_roi_threshold(self, threshold: float) -> None:
        """Set minimum ROI threshold with validation"""
        if not self.validate_roi_threshold(threshold):
            raise ValueError(f"ROI threshold must be between 0 and 1000, got {threshold}")
        self.set('analysis_settings.min_roi_threshold', threshold)
    
    def set_max_cost_price(self, max_cost: float) -> None:
        """Set maximum cost price with validation"""
        if not self.validate_max_cost_price(max_cost):
            raise ValueError(f"Maximum cost price must be between 1 and 10000, got {max_cost}")
        self.set('analysis_settings.max_cost_price', max_cost)
    
    def get_all(self) -> Dict[str, Any]:
        """Get all configuration data"""
        return self.settings.copy()
    
    def save(self, file_path: str = None) -> None:
        """Save configuration to specified file"""
        target_path = file_path or self.config_path
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        with open(target_path, 'w', encoding='utf-8') as f:
            json.dump(self.settings, f, indent=2)
    
    def load(self, file_path: str) -> None:
        """Load configuration from specified file"""
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # Merge with defaults to ensure all required keys exist
                    for key, value in loaded_config.items():
                        self.settings[key] = value
        except (json.JSONDecodeError, IOError):
            # If file is invalid or unreadable, keep current settings
            pass
