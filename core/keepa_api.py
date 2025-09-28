"""
Keepa API integration for Amazon product data
"""

import requests
import json
from typing import Optional, Dict, Any

class KeepaAPI:
    """Interface to Keepa API for Amazon product data"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.keepa.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Amazon-Profitability-Analyzer/1.0'
        })
    
    def get_product_data(self, asin: str, domain: int = 8) -> Optional[Dict[str, Any]]:
        """
        Get product data from Keepa API
        Args:
            asin: Amazon ASIN
            domain: Amazon domain (8 = amazon.fr)
        Returns:
            Dictionary with product data or None if failed
        """
        if not self.api_key:
            raise ValueError("Keepa API key is required")
        
        url = f"{self.base_url}/product"
        params = {
            'key': self.api_key,
            'domain': domain,  # 8 = amazon.fr
            'asin': asin,
            'stats': '180',  # Get 180 days of statistics
            'offers': '20'   # Get current offers
        }
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if 'products' not in data or not data['products']:
                return None
            
            product = data['products'][0]
            return self._parse_product_data(product)
            
        except requests.exceptions.RequestException as e:
            print(f"Keepa API request failed: {e}")
            return None
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            print(f"Failed to parse Keepa response: {e}")
            return None
    
    def _parse_product_data(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """Parse raw Keepa product data into standardized format"""
        
        # Extract current price (in euro cents, convert to euros)
        current_price = 0.0
        if 'csv' in product and product['csv']:
            # csv[1] contains Amazon price history
            # Last price point is the most recent
            amazon_price_data = product['csv'].get(1, [])
            if amazon_price_data and len(amazon_price_data) >= 2:
                # Price is in euro cents, convert to euros
                price_cents = amazon_price_data[-1]
                if price_cents and price_cents != -1:  # -1 means no data
                    current_price = price_cents / 100.0
        
        # Extract product title
        title = product.get('title', 'Unknown Product')
        
        # Extract sales rank
        sales_rank = None
        if 'csv' in product and product['csv']:
            # csv[3] contains sales rank history
            rank_data = product['csv'].get(3, [])
            if rank_data and len(rank_data) >= 2:
                sales_rank = rank_data[-1]
        
        # Extract review count and rating
        review_count = product.get('reviewCount', 0)
        rating = product.get('rating', 0)
        if rating > 0:
            rating = rating / 10.0  # Keepa returns rating * 10
        
        # Extract category info
        category_tree = product.get('categoryTree', [])
        main_category = None
        if category_tree and len(category_tree) > 0:
            # categoryTree[0] might be a dict or another structure
            first_category = category_tree[0]
            if isinstance(first_category, dict):
                main_category = first_category.get('name', 'Unknown')
            else:
                # If it's not a dict, use it as string
                main_category = str(first_category) if first_category else 'Unknown'
        
        # Extract dimensions and weight (if available)
        package_weight = product.get('packageWeight', 500)  # Default 500g
        weight_kg = package_weight / 1000.0 if package_weight else 0.5
        
        # Extract availability
        availability = product.get('availabilityAmazon', 0)
        in_stock = availability >= 0
        
        return {
            'asin': product.get('asin', ''),
            'title': title,
            'current_price': current_price,
            'sales_rank': sales_rank,
            'review_count': review_count,
            'rating': rating,
            'category': main_category,
            'weight': weight_kg,
            'in_stock': in_stock,
            'last_updated': product.get('lastUpdate', 0),
            'raw_data': product  # Keep raw data for advanced analysis
        }
    
    def get_price_history(self, asin: str, domain: int = 8, days: int = 90) -> Optional[Dict[str, Any]]:
        """
        Get price history for a product
        Args:
            asin: Amazon ASIN
            domain: Amazon domain (8 = amazon.fr)
            days: Number of days of history to retrieve
        Returns:
            Dictionary with price history data
        """
        product_data = self.get_product_data(asin, domain)
        if not product_data:
            return None
        
        # Extract price history from raw data
        raw_data = product_data['raw_data']
        price_history = []
        
        if 'csv' in raw_data and raw_data['csv']:
            amazon_price_data = raw_data['csv'].get(1, [])
            
            # Keepa data comes in pairs: [timestamp1, price1, timestamp2, price2, ...]
            for i in range(0, len(amazon_price_data), 2):
                if i + 1 < len(amazon_price_data):
                    timestamp = amazon_price_data[i]
                    price_cents = amazon_price_data[i + 1]
                    
                    if price_cents != -1:  # -1 means no data
                        price_euros = price_cents / 100.0
                        price_history.append({
                            'timestamp': timestamp,
                            'price': price_euros
                        })
        
        return {
            'asin': asin,
            'price_history': price_history,
            'current_price': product_data['current_price']
        }
    
    def test_connection(self) -> bool:
        """Test if API key is valid and connection works"""
        try:
            url = f"{self.base_url}/token"
            params = {'key': self.api_key}
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            return data.get('tokensLeft', 0) >= 0
            
        except Exception:
            return False
