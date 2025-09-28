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
                print(f"Keepa API: No products found for ASIN {asin}")
                return None
            
            product = data['products'][0]
            parsed_data = self._parse_product_data(product)
            
            # Validate that we got meaningful data
            if not parsed_data or not self._validate_product_data(parsed_data):
                print(f"Keepa API: Invalid or incomplete product data for ASIN {asin}")
                return None
                
            return parsed_data
            
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
            csv_data = product['csv']
            
            # Handle both dict and list formats for csv data
            if isinstance(csv_data, dict):
                # csv[1] contains Amazon price history
                # Last price point is the most recent
                amazon_price_data = csv_data.get(1, [])
            elif isinstance(csv_data, list) and len(csv_data) > 1:
                # If csv is a list, try to get index 1
                amazon_price_data = csv_data[1] if len(csv_data) > 1 else []
            else:
                amazon_price_data = []
            
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
            csv_data = product['csv']
            
            # Handle both dict and list formats for csv data
            if isinstance(csv_data, dict):
                # csv[3] contains sales rank history
                rank_data = csv_data.get(3, [])
            elif isinstance(csv_data, list) and len(csv_data) > 3:
                # If csv is a list, try to get index 3
                rank_data = csv_data[3] if len(csv_data) > 3 else []
            else:
                rank_data = []
                
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
            csv_data = raw_data['csv']
            if isinstance(csv_data, dict):
                amazon_price_data = csv_data.get(1, [])
            elif isinstance(csv_data, list) and len(csv_data) > 1:
                amazon_price_data = csv_data[1] if len(csv_data) > 1 else []
            else:
                amazon_price_data = []
            
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
    
    def _validate_product_data(self, product_data: Dict[str, Any]) -> bool:
        """
        Validate that product data contains meaningful information
        Args:
            product_data: Parsed product data dictionary
        Returns:
            True if data is valid and usable, False otherwise
        """
        if not product_data:
            return False
        
        # Check required fields
        required_fields = ['asin', 'title']
        for field in required_fields:
            if field not in product_data or not product_data[field]:
                print(f"Keepa API validation: Missing required field '{field}'")
                return False
        
        # Check that we have either price or useful metadata
        has_price = product_data.get('current_price', 0) > 0
        has_metadata = (
            product_data.get('sales_rank') is not None or
            product_data.get('review_count', 0) > 0 or
            product_data.get('category') is not None
        )
        
        if not has_price and not has_metadata:
            print("Keepa API validation: No price or useful metadata found")
            return False
        
        # Check for reasonable data values
        title = product_data.get('title', '')
        if len(title.strip()) < 3:
            print(f"Keepa API validation: Title too short: '{title}'")
            return False
        
        # Check for placeholder/error titles
        error_indicators = ['unknown', 'not found', 'error', '404', 'unavailable']
        title_lower = title.lower()
        if any(indicator in title_lower for indicator in error_indicators):
            print(f"Keepa API validation: Title indicates error: '{title}'")
            return False
        
        return True
