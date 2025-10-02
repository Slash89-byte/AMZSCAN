"""
Amazon Product Profitability Analyzer

A comprehensive tool for analyzing Amazon product profitability with enhanced features
including multi-format identifier support, comprehensive fee calculations, and
enhanced ROI analysis.
"""

import sys
import os
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.enhanced_main_window import EnhancedMainWindow
from utils.config import Config


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Amazon Profitability Analyzer - Enhanced")
    app.setApplicationVersion("2.1")
    app.setOrganizationName("Amazon Analysis Tools")
    
    # Enable high DPI scaling (PyQt6 compatible)
    try:
        app.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
        app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
    except AttributeError:
        # PyQt6 may not have these attributes - high DPI is handled automatically
        pass
    
    try:
        # Check configuration
        config = Config()
        api_key = config.get('keepa_api_key')
        
        if not api_key:
            QMessageBox.information(
                None, 
                "Welcome to Amazon Profitability Analyzer - Enhanced",
                "Welcome to the Enhanced version! \n\n"
                "New features:\n"
                "• 🖼️ Product image display\n"
                "• 📈 Interactive Keepa price charts\n"
                "• 📊 Enhanced visual results\n"
                "• 📋 Detailed product information panel\n\n"
                "Please configure your Keepa API key through the Configuration menu to get started."
            )
        
        # Create and show enhanced main window
        window = EnhancedMainWindow()
        window.show()
        
        # Start the event loop
        sys.exit(app.exec())
        
    except Exception as e:
        QMessageBox.critical(
            None,
            "Application Error",
            f"Failed to start enhanced application:\n\n{str(e)}\n\n"
            f"If you're missing required packages, please install:\n"
            f"pip install matplotlib pillow"
        )
        sys.exit(1)


if __name__ == '__main__':
    main()

