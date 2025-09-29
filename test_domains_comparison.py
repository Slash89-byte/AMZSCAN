#!/usr/bin/env python3
"""
Test domain parameters to see which is correct for Amazon France
"""

import sys
import os
import requests

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.config import Config

def test_domain_parameters():
    """Test different domain parameters"""
    
    config = Config()
    api_key = config.get('keepa_api_key', '')
    
    if not api_key:
        print("❌ No API key found")
        return
    
    # Test domains for Amazon France
    domains_to_test = [
        {"domain": 4, "name": "Domain 4"},
        {"domain": 8, "name": "Domain 8"},
    ]
    
    asin = "B0BQBXBW88"
    
    for domain_info in domains_to_test:
        print(f"\n{'='*50}")
        print(f"Testing {domain_info['name']} for Amazon France")
        print(f"{'='*50}")
        
        url = "https://api.keepa.com/product"
        params = {
            'key': api_key,
            'domain': domain_info['domain'],
            'asin': asin,
            'stats': 1
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('products'):
                    product = data['products'][0]
                    print(f"✅ Product found")
                    print(f"Title: {product.get('title', 'N/A')}")
                    print(f"Domain ID: {product.get('domainId', 'N/A')}")
                    
                    # Check CSV data
                    csv_data = product.get('csv', [])
                    if isinstance(csv_data, list):
                        # Check Amazon price (csv[1])
                        if len(csv_data) > 1 and csv_data[1]:
                            amazon_prices = csv_data[1]
                            if len(amazon_prices) >= 2:
                                latest_price = amazon_prices[-1]
                                if latest_price and latest_price != -1:
                                    price_eur = latest_price / 100
                                    print(f"Amazon Price (csv[1]): €{price_eur:.2f}")
                        
                        # Check Buy Box price (csv[0])
                        if len(csv_data) > 0 and csv_data[0]:
                            buybox_prices = csv_data[0]
                            if len(buybox_prices) >= 2:
                                latest_price = buybox_prices[-1]
                                if latest_price and latest_price != -1:
                                    price_eur = latest_price / 100
                                    print(f"Buy Box Price (csv[0]): €{price_eur:.2f}")
                                else:
                                    print(f"Buy Box Price (csv[0]): No current price")
                            else:
                                print(f"Buy Box Price (csv[0]): No data")
                        else:
                            print(f"Buy Box Price (csv[0]): No data")
                else:
                    print("❌ No products found")
            else:
                print(f"❌ Request failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_domain_parameters()
