# Amazon Profitability Analyzer

A PyQt6 desktop application for analyzing Amazon product profitability using Keepa API integration.

## Features

- **ROI Calculator**: Input ASIN + cost price → Get instant profitability analysis
- **Amazon France Support**: Accurate fee calculations for Amazon.fr marketplace
- **Keepa Integration**: Real-time product data and pricing
- **Professional GUI**: Clean, easy-to-use desktop interface
- **Configurable Thresholds**: Customize ROI requirements

## Installation

1. **Clone or download** this project
2. **Install Python packages**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Get a Keepa API key** from https://keepa.com/#!api
4. **Configure the application**:
   - Copy `config.json.example` to `config.json`
   - Add your Keepa API key to the config file

## Usage

### GUI Application
```bash
python main.py
```

### Test Core Functionality
```bash
python test_functionality.py
```

## How It Works

1. **Enter an ASIN** and your **cost price**
2. Click **"Analyze Profitability"**
3. Get instant results:
   - Current Amazon price
   - Amazon fees breakdown
   - Your profit margin
   - ROI percentage
   - ✅/❌ Profitability decision

## Example Analysis

```
Product Price: €29.99
Your Cost: €15.00
Amazon Fees: €7.30
Profit: €7.69
ROI: 51.3% ✅ PROFITABLE
```

## Configuration

Edit `config.json` to customize:
- API keys
- ROI threshold (default: 15%)
- Marketplace settings
- Fee calculations

## Requirements

- Python 3.7+
- PyQt6
- Keepa API subscription
- Internet connection
