"""
Main Dashboard Window for Amazon Analysis Tools.
Provides access to both Profit Analyzer and Qogita Brand Scanner modules.
"""

import sys
import os
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QStackedWidget, QPushButton, QLabel, QFrame,
                             QApplication, QMessageBox, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap, QIcon

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gui.enhanced_main_window import EnhancedMainWindow
from gui.settings_dialog import SettingsDialog
from utils.config import Config


class ModuleSelectorWidget(QWidget):
    """Widget for selecting between different analysis modules"""
    
    module_selected = pyqtSignal(str)  # Signal emitted when module is selected
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the module selector UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(30)
        layout.setContentsMargins(50, 50, 50, 50)
        
        # Title
        title = QLabel("Amazon Analysis Tools")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #2c3e50; margin-bottom: 20px;")
        layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("Choose your analysis module")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_font = QFont()
        subtitle_font.setPointSize(12)
        subtitle.setFont(subtitle_font)
        subtitle.setStyleSheet("color: #7f8c8d; margin-bottom: 30px;")
        layout.addWidget(subtitle)
        
        # Module buttons container
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(40)
        
        # Profit Analyzer Module
        profit_analyzer_btn = self.create_module_button(
            "💰 Profit Analyzer",
            "Single Product Analysis",
            [
                "• Amazon product lookup",
                "• Keepa price history charts",
                "• Comprehensive fee calculations",
                "• ROI and profit analysis",
                "• Enhanced visual interface"
            ],
            "profit_analyzer"
        )
        buttons_layout.addWidget(profit_analyzer_btn)
        
        # Qogita Brand Scanner Module
        qogita_scanner_btn = self.create_module_button(
            "🧴 Qogita Brand Scanner",
            "Bulk Brand Analysis",
            [
                "• Brand-based product discovery",
                "• Wholesale price integration",
                "• Bulk profitability analysis",
                "• Amazon product matching",
                "• Export and filtering tools"
            ],
            "qogita_scanner"
        )
        buttons_layout.addWidget(qogita_scanner_btn)
        
        layout.addLayout(buttons_layout)
        
        # Footer info
        footer = QLabel("Select a module to begin your analysis")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setStyleSheet("color: #95a5a6; font-style: italic; margin-top: 30px;")
        layout.addWidget(footer)
        
        layout.addStretch()
    
    def create_module_button(self, title: str, subtitle: str, features: list, module_id: str) -> QPushButton:
        """Create a styled module selection button"""
        btn = QPushButton()
        btn.setFixedSize(350, 400)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(lambda: self.module_selected.emit(module_id))
        
        # Create button content
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #2c3e50;")
        layout.addWidget(title_label)
        
        # Subtitle
        subtitle_label = QLabel(subtitle)
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_font = QFont()
        subtitle_font.setPointSize(11)
        subtitle_font.setBold(True)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setStyleSheet("color: #3498db; margin-bottom: 10px;")
        layout.addWidget(subtitle_label)
        
        # Features list
        for feature in features:
            feature_label = QLabel(feature)
            feature_label.setWordWrap(True)
            feature_label.setStyleSheet("color: #34495e; padding: 2px 0px;")
            layout.addWidget(feature_label)
        
        layout.addStretch()
        
        # Set button style
        btn.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                border: 2px solid #e0e6ed;
                border-radius: 10px;
                padding: 0px;
            }
            QPushButton:hover {
                border-color: #3498db;
                background-color: #f8f9fa;
            }
            QPushButton:pressed {
                background-color: #e3f2fd;
                border-color: #2980b9;
            }
        """)
        
        # Set the widget as the button's content
        btn_layout = QVBoxLayout(btn)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.addWidget(widget)
        
        return btn


class MainDashboardWindow(QMainWindow):
    """Main dashboard window with module selection and navigation"""
    
    def __init__(self):
        super().__init__()
        self.profit_analyzer_window = None
        self.qogita_scanner_window = None
        self.setup_ui()
        self.setup_window()
    
    def setup_window(self):
        """Configure main window properties"""
        self.setWindowTitle("Amazon Analysis Tools - Dashboard")
        self.setMinimumSize(800, 600)
        self.resize(1000, 700)
        
        # Center the window
        self.center_window()
        
        # Set window icon (if available)
        try:
            self.setWindowIcon(QIcon("assets/icon.png"))
        except:
            pass
    
    def center_window(self):
        """Center the window on the screen"""
        from PyQt6.QtGui import QGuiApplication
        screen = QGuiApplication.primaryScreen().geometry()
        size = self.geometry()
        self.move(
            (screen.width() - size.width()) // 2,
            (screen.height() - size.height()) // 2
        )
    
    def setup_ui(self):
        """Set up the main dashboard UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Navigation bar
        nav_bar = self.create_navigation_bar()
        layout.addWidget(nav_bar)
        
        # Stacked widget for different views
        self.stacked_widget = QStackedWidget()
        layout.addWidget(self.stacked_widget)
        
        # Module selector (home page)
        self.module_selector = ModuleSelectorWidget()
        self.module_selector.module_selected.connect(self.open_module)
        self.stacked_widget.addWidget(self.module_selector)
        
        # Set initial view
        self.stacked_widget.setCurrentWidget(self.module_selector)
    
    def create_navigation_bar(self) -> QFrame:
        """Create the top navigation bar"""
        nav_frame = QFrame()
        nav_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        nav_frame.setFixedHeight(60)
        nav_frame.setStyleSheet("""
            QFrame {
                background-color: #34495e;
                border: none;
                border-bottom: 2px solid #2c3e50;
            }
        """)
        
        layout = QHBoxLayout(nav_frame)
        layout.setContentsMargins(20, 10, 20, 10)
        
        # Logo/Brand
        brand = QLabel("🔍 Amazon Analysis Tools")
        brand.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        layout.addWidget(brand)
        
        layout.addStretch()
        
        # Navigation buttons
        home_btn = QPushButton("🏠 Home")
        home_btn.clicked.connect(self.show_home)
        home_btn.setStyleSheet(self.get_nav_button_style())
        layout.addWidget(home_btn)
        
        # Config button (if needed)
        config_btn = QPushButton("⚙️ Settings")
        config_btn.clicked.connect(self.show_settings)
        config_btn.setStyleSheet(self.get_nav_button_style())
        layout.addWidget(config_btn)
        
        return nav_frame
    
    def get_nav_button_style(self) -> str:
        """Get navigation button styling"""
        return """
            QPushButton {
                background-color: transparent;
                color: white;
                border: 1px solid #5d6d7e;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5d6d7e;
            }
            QPushButton:pressed {
                background-color: #4a5a6b;
            }
        """
    
    def show_home(self):
        """Show the home/module selector page"""
        self.stacked_widget.setCurrentWidget(self.module_selector)
        self.setWindowTitle("Amazon Analysis Tools - Dashboard")
    
    def show_settings(self):
        """Show settings/configuration dialog"""
        try:
            settings_dialog = SettingsDialog(parent=self)
            settings_dialog.exec()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Settings Error",
                f"Failed to open settings dialog:\n{str(e)}"
            )
    
    def open_module(self, module_id: str):
        """Open the selected module"""
        if module_id == "profit_analyzer":
            self.open_profit_analyzer()
        elif module_id == "qogita_scanner":
            self.open_qogita_scanner()
    
    def open_profit_analyzer(self):
        """Open the Profit Analyzer module"""
        try:
            # Check if window exists and is valid
            if self.profit_analyzer_window is None or not self.profit_analyzer_window.isVisible():
                self.profit_analyzer_window = EnhancedMainWindow()
            
            self.profit_analyzer_window.show()
            self.profit_analyzer_window.raise_()
            self.profit_analyzer_window.activateWindow()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to open Profit Analyzer:\n\n{str(e)}"
            )
    
    def open_qogita_scanner(self):
        """Open the Qogita Brand Scanner module"""
        try:
            # Import here to avoid circular imports
            from gui.qogita_scanner import QogitaScannerWindow
            
            # Check if window exists and is valid
            if self.qogita_scanner_window is None or not self.qogita_scanner_window.isVisible():
                self.qogita_scanner_window = QogitaScannerWindow()
            
            self.qogita_scanner_window.show()
            self.qogita_scanner_window.raise_()
            self.qogita_scanner_window.activateWindow()
            
        except ImportError:
            QMessageBox.information(
                self,
                "Coming Soon",
                "Qogita Brand Scanner is being implemented!\n\n"
                "This module will provide:\n"
                "• Brand-based product discovery\n"
                "• Bulk profitability analysis\n"
                "• Wholesale price integration\n\n"
                "Implementation in progress..."
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error", 
                f"Failed to open Qogita Scanner:\n\n{str(e)}"
            )
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Close child windows
        if self.profit_analyzer_window:
            self.profit_analyzer_window.close()
        if self.qogita_scanner_window:
            self.qogita_scanner_window.close()
        
        event.accept()


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Amazon Analysis Tools")
    app.setApplicationVersion("3.0")
    app.setOrganizationName("Amazon Analysis Tools")
    
    # Enable high DPI scaling
    try:
        app.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
        app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
    except AttributeError:
        # PyQt6 handles high DPI automatically
        pass
    
    try:
        # Check configuration
        config = Config()
        
        # Create and show main dashboard
        dashboard = MainDashboardWindow()
        dashboard.show()
        
        # Start the event loop
        sys.exit(app.exec())
        
    except Exception as e:
        QMessageBox.critical(
            None,
            "Application Error",
            f"Failed to start application:\n\n{str(e)}"
        )
        sys.exit(1)


if __name__ == '__main__':
    main()
