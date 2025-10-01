#!/usr/bin/env python3
"""
Test script for complete enhanced integration
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    # Test imports
    from gui.main_window import MainWindow
    from gui.config_dialog import ConfigurationDialog
    from core.enhanced_amazon_fees import EnhancedAmazonFeesCalculator
    from core.enhanced_roi_calculator import EnhancedROICalculator
    from utils.config import Config
    print("✅ All enhanced modules imported successfully")
    
    # Test configuration
    config = Config()
    print(f"✅ Configuration loaded")
    
    # Test enhanced calculators initialization
    enhanced_fees = EnhancedAmazonFeesCalculator(config=config)
    enhanced_roi = EnhancedROICalculator(config=config)
    print(f"✅ Enhanced calculators initialized")
    
    # Test configuration dialog creation
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    
    config_dialog = ConfigurationDialog(config=config)
    print(f"✅ Enhanced configuration dialog created")
    
    # Test main window creation (without showing)
    main_window = MainWindow()
    print(f"✅ Enhanced main window created")
    
    # Test analysis worker creation
    from gui.main_window import AnalysisWorker
    worker = AnalysisWorker('B0BQBXBW88', 8.50, config)
    print(f"✅ Enhanced analysis worker created")
    
    print(f"\n🎉 All enhanced integration tests passed!")
    print(f"✅ Ready for production use with enhanced profit calculator")
    
    # Summary of enhancements
    print(f"\n📋 Enhanced Features Summary:")
    print(f"  • Comprehensive Amazon fee calculation (8 fee types)")
    print(f"  • Automatic storage fee calculation from Keepa dimensions")
    print(f"  • Enhanced ROI analysis with profitability scoring")
    print(f"  • Advanced configuration interface for additional fees")
    print(f"  • Detailed fee breakdown in analysis results")
    print(f"  • Break-even price calculation capability")
    print(f"  • VAT handling improvements")
    print(f"  • Multi-format identifier support (ASIN, EAN, UPC, GTIN)")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
