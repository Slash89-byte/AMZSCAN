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
        self.base_url = "https://api.keepa.com/"
        
        # Category mapping for Amazon fee calculations
        self.category_mappings = {
            'beauté et parfum': 'beauty',
            'beauty': 'beauty',
            'beauté': 'beauty',
            'parfum': 'beauty',
            'cosmetics': 'beauty',
            'electronics': 'electronics',
            'informatique': 'electronics',
            'électronique': 'electronics',
            'books': 'books',
            'livres': 'books',
            'clothing': 'clothing',
            'vêtements': 'clothing',
            'mode': 'clothing',
            'sports': 'sports',
            'sport': 'sports',
            'toys': 'toys',
            'jouets': 'toys',
            'home': 'home_garden',
            'maison': 'home_garden',
            'jardin': 'home_garden',
        }
    
    def get_product_data(self, asin: str, domain: int = 8) -> Optional[Dict[str, Any]]:
        """
        Get product data from Keepa API
        Args:
            asin: Amazon ASIN
            domain: Amazon domain (8 = amazon.fr)
        Returns:
            Dictionary with product data or None if error
        """
        try:
            url = f"{self.base_url}product"
            params = {
                'key': self.api_key,
                'domain': domain,
                'asin': asin,
                'stats': 1
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'products' not in data or not data['products']:
                return None
            
            product = data['products'][0]
            return self._parse_product_data(product)
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from Keepa: {e}")
            return None
        except (KeyError, ValueError) as e:
            print(f"Error parsing Keepa response: {e}")
            return None
    
    def _parse_product_data(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """Parse raw Keepa product data into our format"""
        
        # Validate that we have the essential data
        if not self._validate_product_data(product):
            return None
        
        # Extract current price from Amazon price history
        current_price = 0.0
        if 'csv' in product and product['csv']:
            csv_data = product['csv']
            
            # Handle both dict and list formats for csv data
            if isinstance(csv_data, dict):
                # csv[1] contains Amazon price history
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
        
        # Determine fee category
        fee_category = self._get_fee_category(main_category)
        
        return {
            'asin': product.get('asin', ''),
            'title': title,
            'current_price': current_price,
            'sales_rank': sales_rank,
            'review_count': review_count,
            'rating': rating,
            'category': main_category,
            'fee_category': fee_category,  # Category for fee calculations
            'weight': weight_kg,
            'in_stock': in_stock,
            'last_updated': product.get('lastUpdate', 0),
            'raw_data': product  # Keep raw data for advanced analysis
        }
    
    def _get_fee_category(self, category_name: str) -> str:
        """
        Map a product category name to Amazon fee calculation category
        
        Args:
            category_name: The category name from Keepa
            
        Returns:
            Category name for fee calculations
        """
        if not category_name:
            return 'default'
        
        # Convert to lowercase for matching
        category_lower = category_name.lower()
        
        # Check for exact matches first
        if category_lower in self.category_mappings:
            return self.category_mappings[category_lower]
        
        # Check for partial matches
        for keyword, fee_category in self.category_mappings.items():
            if keyword in category_lower:
                return fee_category
        
        # Default if no match found
        return 'default'
    
    def _validate_product_data(self, product: Dict[str, Any]) -> bool:
        """
        Validate that product data contains essential information
        
        Args:
            product: Raw product data from Keepa
            
        Returns:
            True if data is valid, False otherwise
        """
        # Check if we have basic product information
        if not isinstance(product, dict):
            return False
        
        # Must have an ASIN
        if not product.get('asin'):
            return False
        
        # Must have some price or category data
        has_csv_data = 'csv' in product and product['csv']
        has_category_data = 'categoryTree' in product and product['categoryTree']
        
        if not (has_csv_data or has_category_data):
            return False
        
        return True
    
    def get_price_history(self, asin: str, domain: int = 8, days: int = 90) -> Optional[Dict[str, Any]]:
        """
        Get price history for a product
        Args:
            asin: Amazon ASIN
            domain: Amazon domain (8 = amazon.fr)
            days: Number of days of history to retrieve
        Returns:
            Dictionary with price history or None if error
        """
        try:
            url = f"{self.base_url}product"
            params = {
                'key': self.api_key,
                'domain': domain,
                'asin': asin,
                'history': 1,
                'days': days
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'products' not in data or not data['products']:
                return None
                
            product = data['products'][0]
            
            # Extract price history from CSV data
            price_history = []
            if 'csv' in product and product['csv']:
                csv_data = product['csv']
                
                # Handle both dict and list formats
                if isinstance(csv_data, dict):
                    amazon_prices = csv_data.get(1, [])
                elif isinstance(csv_data, list) and len(csv_data) > 1:
                    amazon_prices = csv_data[1]
                else:
                    amazon_prices = []
                
                # Convert price data to readable format
                for i in range(0, len(amazon_prices), 2):
                    if i + 1 < len(amazon_prices):
                        timestamp = amazon_prices[i]
                        price_cents = amazon_prices[i + 1]
                        if price_cents != -1:  # -1 means no data
                            price_history.append({
                                'timestamp': timestamp,
                                'price': price_cents / 100.0
                            })
            
            return {
                'asin': product.get('asin', ''),
                'price_history': price_history,
                'current_price': price_history[-1]['price'] if price_history else 0.0
            }
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching price history: {e}")
            return None
        except (KeyError, ValueError) as e:
            print(f"Error parsing price history: {e}")
            return None
