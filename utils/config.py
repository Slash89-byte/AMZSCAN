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
            'keepa_api_key': '',
            'min_roi_threshold': 15.0,
            'amazon_marketplace': 'france',
            'default_weight_kg': 0.5,
            'default_category': 'default',
            'currency_symbol': '€',
            'vat_rate': 0.20,
            'ui_settings': {
                'window_width': 800,
                'window_height': 600,
                'theme': 'default'
            },
            'api_settings': {
                'request_timeout': 30,
                'max_retries': 3,
                'rate_limit_delay': 1.0
            }
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
                'domain_id': 8,
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
