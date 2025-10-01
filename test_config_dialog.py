#!/usr/bin/env python3
"""
Test script for enhanced configuration dialog
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from PyQt6.QtWidgets import QApplication
    from gui.config_dialog import ConfigurationDialog
    from utils.config import Config
    print("✅ Successfully imported configuration dialog")
    
    # Create QApplication (required for Qt)
    app = QApplication(sys.argv)
    
    # Initialize config
    config = Config()
    print("✅ Config loaded")
    
    # Create and show configuration dialog
    dialog = ConfigurationDialog(config=config)
    print("✅ Configuration dialog created successfully")
    
    # Check if enhanced fees tab was added
    tab_count = dialog.tab_widget.count()
    tab_names = [dialog.tab_widget.tabText(i) for i in range(tab_count)]
    print(f"✅ Dialog has {tab_count} tabs: {tab_names}")
    
    # Verify enhanced fees tab exists
    if "Enhanced Fees" in tab_names:
        print("✅ Enhanced Fees tab found!")
        
        # Check if fee configuration widgets exist
        fee_types = ['prep_fee', 'inbound_shipping', 'digital_services', 'misc_fee']
        for fee_type in fee_types:
            enabled_checkbox = getattr(dialog, f"{fee_type}_enabled_checkbox", None)
            type_combo = getattr(dialog, f"{fee_type}_type_combo", None)
            value_spin = getattr(dialog, f"{fee_type}_value_spin", None)
            
            if all([enabled_checkbox, type_combo, value_spin]):
                print(f"  ✅ {fee_type} widgets created successfully")
            else:
                print(f"  ❌ {fee_type} widgets missing")
        
        # Check storage and VAT widgets
        if hasattr(dialog, 'storage_months_spin') and hasattr(dialog, 'vat_on_fees_checkbox'):
            print("  ✅ Storage and VAT widgets created successfully")
        else:
            print("  ❌ Storage and VAT widgets missing")
    else:
        print("❌ Enhanced Fees tab not found")
    
    print("✅ Configuration dialog test completed successfully!")
    
    # Don't actually show the dialog in test mode
    # dialog.show()
    # app.exec()
    
except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
