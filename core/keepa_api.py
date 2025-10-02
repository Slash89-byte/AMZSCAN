"""
Keepa API integration for Amazon product data
"""

import requests
import json
import time
from typing import Optional, Dict, Any

class KeepaAPI:
    """Interface to Keepa API for Amazon product data"""
    
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("Keepa API key is required")
        self.api_key = api_key
        self.base_url = "https://api.keepa.com"  # Removed trailing slash
        self.session = requests.Session()  # Add session for test compatibility
        self.session.headers.update({
            'User-Agent': 'Amazon-Profitability-Analyzer/1.0'
        })
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 1.0  # Minimum 1 second between requests (more conservative)
        self.request_count = 0
        self.request_limit_per_minute = 30  # Very conservative limit (Keepa allows 100/min but let's be safe)
        self.minute_start = time.time()
        
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
    
    def _rate_limit(self):
        """Implement rate limiting to prevent 429 errors"""
        current_time = time.time()
        
        # Reset counter every minute
        if current_time - self.minute_start >= 60:
            self.request_count = 0
            self.minute_start = current_time
        
        # Check if we've hit the per-minute limit
        if self.request_count >= self.request_limit_per_minute:
            sleep_time = 60 - (current_time - self.minute_start)
            if sleep_time > 0:
                print(f"Rate limit reached. Waiting {sleep_time:.1f} seconds...")
                time.sleep(sleep_time)
                self.request_count = 0
                self.minute_start = time.time()
        
        # Ensure minimum interval between requests
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
        self.request_count += 1
    
    def _make_request(self, url: str, params: dict, timeout: int = 10, max_retries: int = 3):
        """Make a rate-limited request with retry logic for 429 errors"""
        for attempt in range(max_retries):
            try:
                self._rate_limit()
                response = self.session.get(url, params=params, timeout=timeout)
                
                if response.status_code == 429:
                    # Check for Retry-After header
                    retry_after = response.headers.get('Retry-After')
                    if retry_after:
                        try:
                            wait_time = int(retry_after)
                            print(f"Rate limited (429). Server says retry after {wait_time} seconds...")
                        except ValueError:
                            wait_time = min(10, 2 ** attempt)  # Fallback to exponential backoff
                    else:
                        wait_time = min(10, 2 ** attempt)  # Cap at 10 seconds: 2s, 4s, 8s
                        
                    print(f"Rate limited (429). Waiting {wait_time} seconds before retry {attempt + 1}/{max_retries}...")
                    time.sleep(wait_time)
                    # Reset rate limiting counters after a 429
                    self.request_count = max(0, self.request_count - 5)  # Back off more aggressively
                    continue
                
                response.raise_for_status()
                return response
                
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:  # Last attempt
                    raise e
                print(f"Request failed (attempt {attempt + 1}/{max_retries}): {e}")
                time.sleep(1)  # Wait before retry
        
        raise requests.exceptions.RequestException("Max retries exceeded")

    def get_product_data(self, product_id: str, domain: int = 4) -> Optional[Dict[str, Any]]:
        """
        Get product data from Keepa API
        Args:
            product_id: Product identifier (ASIN, EAN, UPC, GTIN)
            domain: Amazon domain (4 = amazon.fr)
        Returns:
            Dictionary with product data or None if error
        """
        try:
            url = f"{self.base_url}/product"
            
            # Determine identifier type and set appropriate parameter
            from utils.identifiers import detect_and_validate_identifier
            result = detect_and_validate_identifier(product_id)
            
            if not result['is_valid']:
                print(f"Invalid product identifier: {product_id}")
                return {'success': False, 'error': f'Invalid product identifier: {product_id}'}

            params = {
                'key': self.api_key,
                'domain': domain,
                'stats': 1
            }
            
            # Use appropriate parameter based on identifier type
            identifier_type = result['identifier_type']
            normalized_id = result['normalized_code']
            
            if identifier_type == "ASIN":
                params['asin'] = normalized_id
            elif identifier_type in ["EAN", "UPC", "GTIN"]:
                # Keepa API supports EAN/UPC/GTIN lookup
                params['code'] = normalized_id
            else:
                print(f"Unsupported identifier type for Keepa API: {identifier_type}")
                return {'success': False, 'error': f'Unsupported identifier type: {identifier_type}'}
            
            response = self._make_request(url, params, timeout=10)
            data = response.json()
            
            if 'products' not in data or not data['products']:
                return {'success': False, 'error': 'No product data found'}
            
            product = data['products'][0]
            result = self._parse_product_data(product)
            if result is None:
                return {'success': False, 'error': 'Failed to parse product data'}
            return result
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from Keepa: {e}")
            return {'success': False, 'error': f'Request failed: {str(e)}'}
        except (KeyError, ValueError) as e:
            print(f"Error parsing Keepa response: {e}")
            return {'success': False, 'error': f'Parse error: {str(e)}'}
    
    def _parse_product_data(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """Parse raw Keepa product data into our format"""
        
        # For tests, we should always return a dictionary, even if minimal
        if not isinstance(product, dict):
            return None
        
        # Must have an ASIN at minimum
        if 'asin' not in product:
            return None
        
        # Extract current price - prioritize most relevant selling price for profitability analysis
        current_price = 0.0
        
        # First try stats.current array for real-time prices
        if 'stats' in product and product['stats']:
            stats = product['stats']
            if 'current' in stats and isinstance(stats['current'], list):
                current_stats = stats['current']
                # Priority order for seller profitability analysis:
                # 1. Buy Box price (index 0) - what customers actually see and pay
                # 2. New FBA price (index 4) - what FBA sellers charge (most relevant for competition)
                # 3. Amazon price (index 1) - Amazon's direct price (if they're selling)
                # 4. New 3rd party price (index 2) - other sellers
                
                price_priorities = [0, 4, 1, 2]  # Buy Box, New FBA, Amazon, New 3rd Party
                
                for price_index in price_priorities:
                    if len(current_stats) > price_index and current_stats[price_index] != -1:
                        current_price = current_stats[price_index] / 100.0
                        break
        
        # Fallback to csv data if stats not available
        if current_price == 0.0 and 'csv' in product and product['csv']:
            csv_data = product['csv']
            
            # Handle both dict and list formats for csv data
            if isinstance(csv_data, list):
                # Priority order: Buy Box (0), New FBA (4), Amazon (1), New 3rd Party (2)
                price_priorities = [0, 4, 1, 2]
                
                for price_index in price_priorities:
                    if len(csv_data) > price_index and csv_data[price_index]:
                        price_array = csv_data[price_index]
                        if price_array and len(price_array) >= 2:
                            price_cents = price_array[-1]
                            if price_cents and price_cents != -1:  # -1 means no data
                                current_price = price_cents / 100.0
                                break
            elif isinstance(csv_data, dict):
                # Handle dict format as fallback
                price_priorities = [0, 4, 1, 2]
                
                for price_index in price_priorities:
                    price_data = csv_data.get(price_index, [])
                    if price_data and len(price_data) >= 2:
                        price_cents = price_data[-1]
                        if price_cents and price_cents != -1:
                            current_price = price_cents / 100.0
                            break
        
        # Extract product title
        title = product.get('title', 'Unknown Product')
        
        # Extract product image URL
        image_url = None
        if 'imagesCSV' in product and product['imagesCSV']:
            # Get first image from CSV
            images_csv = product['imagesCSV'].split(',')
            if images_csv:
                image_filename = images_csv[0].strip()
                if image_filename:
                    image_url = f"https://images-na.ssl-images-amazon.com/images/I/{image_filename}"
        
        # Extract sales rank from stats or csv
        sales_rank = None
        if 'stats' in product and product['stats'] and 'current' in product['stats']:
            current_stats = product['stats']['current']
            if isinstance(current_stats, list) and len(current_stats) > 3:
                # current[3] typically contains sales rank
                rank_value = current_stats[3]
                if rank_value and rank_value != -1:
                    sales_rank = rank_value
        
        # Fallback to csv data for sales rank
        if sales_rank is None and 'csv' in product and product['csv']:
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
        
        # Also check the 'type' field for category
        if not main_category and 'type' in product and product['type']:
            main_category = product['type'].replace('_', ' ').title()
        
        # Extract dimensions and weight (if available)
        package_weight = product.get('packageWeight', 500)  # Default 500g
        weight_kg = package_weight / 1000.0 if package_weight else 0.5
        
        # Extract availability
        availability = product.get('availabilityAmazon', 0)
        in_stock = availability >= 0
        
        # Extract price history for charts
        price_history = []
        if 'csv' in product and product['csv']:
            csv_data = product['csv']
            # CSV data is a list where index 1 contains Amazon price history
            if isinstance(csv_data, list) and len(csv_data) > 1:
                amazon_price_data = csv_data[1]
                if amazon_price_data and len(amazon_price_data) >= 2:
                    # Price data comes in pairs: [timestamp, price, timestamp, price, ...]
                    for i in range(0, len(amazon_price_data), 2):
                        if i + 1 < len(amazon_price_data):
                            timestamp = amazon_price_data[i]
                            price_cents = amazon_price_data[i + 1]
                            if price_cents != -1:  # -1 means no data
                                price_history.append({
                                    'timestamp': timestamp,
                                    'price': price_cents / 100.0
                                })
            elif isinstance(csv_data, dict) and 1 in csv_data:
                # Handle dict format as fallback
                amazon_price_data = csv_data[1]
                if amazon_price_data and len(amazon_price_data) >= 2:
                    for i in range(0, len(amazon_price_data), 2):
                        if i + 1 < len(amazon_price_data):
                            timestamp = amazon_price_data[i]
                            price_cents = amazon_price_data[i + 1]
                            if price_cents != -1:
                                price_history.append({
                                    'timestamp': timestamp,
                                    'price': price_cents / 100.0
                                })
        
        # Determine fee category
        fee_category = self._get_fee_category(main_category)
        
        return {
            'success': True,  # Add success flag
            'data': {
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
                'image_url': image_url,
                'price_history': price_history,
                'last_updated': product.get('lastUpdate', 0),
                'raw_data': product  # Keep raw data for advanced analysis
            },
            'error': None
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
    
    def get_price_history(self, asin: str, domain: int = 4, days: int = 90) -> Optional[Dict[str, Any]]:
        """
        Get price history for a product
        Args:
            asin: Amazon ASIN
            domain: Amazon domain (4 = amazon.fr)
            days: Number of days of history to retrieve
        Returns:
            Dictionary with price history or None if error
        """
        try:
            url = f"{self.base_url}/product"
            params = {
                'key': self.api_key,
                'domain': domain,
                'asin': asin,
                'history': 1,
                'days': days
            }
            
            response = self._make_request(url, params, timeout=10)
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
    
    def search_products(self, query: str, domain: str = 'fr') -> Optional[list]:
        """
        Search for products using Keepa API search functionality
        
        Args:
            query: Search query string
            domain: Amazon domain (fr, com, de, etc.)
            
        Returns:
            List of search results or None if search fails
        """
        try:
            # Convert domain string to domain code
            domain_codes = {
                'com': 1, 'co.uk': 2, 'de': 3, 'fr': 4, 'co.jp': 5,
                'ca': 6, 'it': 7, 'es': 8, 'in': 9, 'mx': 10
            }
            
            domain_code = domain_codes.get(domain, 4)  # Default to France
            
            # Use Keepa's search endpoint
            url = f"{self.base_url}/search"
            params = {
                'key': self.api_key,
                'domain': domain_code,
                'type': 'product',
                'term': query,
                'page': 0,
                'perPage': 50,
                'sort': 0  # Sort by relevance
            }
            
            response = self._make_request(url, params, timeout=15)
            data = response.json()
            
            # Check for successful response
            if not data.get('products'):
                return []
                
            # Format results for compatibility
            results = []
            for product in data['products']:
                if product.get('asin'):
                    results.append({
                        'asin': product['asin'],
                        'title': product.get('title', ''),
                        'domain': domain_code
                    })
            
            return results
            
        except Exception as e:
            print(f"Error searching products: {e}")
            return None

    def test_connection(self) -> bool:
        """
        Test the connection to Keepa API
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            url = f"{self.base_url}/token"
            params = {'key': self.api_key}
            
            response = self._make_request(url, params, timeout=10)
            data = response.json()
            # Check if we have tokens left (positive number indicates valid key)
            return data.get('tokensLeft', 0) > 0
            
        except Exception:
            return False
