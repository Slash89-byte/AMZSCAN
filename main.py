"""
Amazon Product Profitability Analyzer

A comprehensive tool for analyzing Amazon product profitability with enhanced features
including multi-format identifier support, comprehensive fee calculations, enhanced ROI analysis,
and Qogita wholesale product discovery.
"""

import sys
import os
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.main_dashboard import MainDashboardWindow
from utils.config import Config


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Amazon Analysis Tools")
    app.setApplicationVersion("3.0")
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
                "Welcome to Amazon Analysis Tools v3.0",
                "Welcome to the new unified platform! \n\n"
                "Available modules:\n"
                "• 💰 Profit Analyzer - Single product analysis\n"
                "• 🧴 Qogita Brand Scanner - Bulk brand analysis\n\n"
                "Features:\n"
                "• 🖼️ Product image display\n"
                "• 📈 Interactive Keepa price charts\n"
                "• 📊 Enhanced visual results\n"
                "• � Wholesale product discovery\n"
                "• 📋 Bulk profitability analysis\n\n"
                "Please configure your API keys through the Settings menu to get started."
            )
        
        # Create and show main dashboard
        dashboard = MainDashboardWindow()
        dashboard.show()
        
        # Start the event loop
        sys.exit(app.exec())
        
    except Exception as e:
        QMessageBox.critical(
            None,
            "Application Error",
            f"Failed to start application:\n\n{str(e)}\n\n"
            f"If you're missing required packages, please install:\n"
            f"pip install matplotlib pillow"
        )
        sys.exit(1)


if __name__ == '__main__':
    main()

