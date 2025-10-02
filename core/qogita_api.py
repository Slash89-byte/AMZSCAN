"""
Qogita API integration for wholesale product discovery and pricing.
Handles authentication, brand-based product search via CSV catalog download, and cart management.
"""

import requests
import logging
import csv
from io import StringIO
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import time

logger = logging.getLogger(__name__)


class QogitaAPIError(Exception):
    """Custom exception for Qogita API errors."""
    pass


class QogitaRateLimitError(QogitaAPIError):
    """Custom exception for rate limit errors."""
    def __init__(self, message: str, retry_after: int = None):
        super().__init__(message)
        self.retry_after = retry_after


class QogitaAPI:
    """Interface for Qogita API operations."""
    
    def __init__(self, email: str, password: str):
        self.base_url = "https://api.qogita.com"
        self.email = email
        self.password = password
        self.access_token = None
        self.cart_qid = None
        self.token_expires_at = None
        self.session = requests.Session()
        self.last_request_time = 0
        self.min_request_interval = 1.0  # Minimum seconds between requests
        
    def authenticate(self) -> bool:
        """
        Authenticate with Qogita API using email/password.
        Returns True if successful, False otherwise.
        """
        try:
            logger.info("Authenticating with Qogita API...")
            
            response = self.session.post(
                url=f"{self.base_url}/auth/login/",
                json={
                    "email": self.email,
                    "password": self.password
                }
            )
            
            if response.status_code != 200:
                logger.error(f"Authentication failed: {response.status_code} - {response.text}")
                raise QogitaAPIError(f"Authentication failed: {response.status_code}")
            
            data = response.json()
            
            # Extract access token and cart information
            self.access_token = data.get("accessToken")
            if not self.access_token:
                raise QogitaAPIError("No access token received from Qogita API")
            
            # Set up authorization header for future requests
            self.session.headers.update({
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            })
            
            # Get active cart QID
            user_data = data.get("user", {})
            self.cart_qid = user_data.get("activeCartQid")
            
            # Estimate token expiration (assume 24 hours if not specified)
            self.token_expires_at = datetime.now() + timedelta(hours=24)
            
            logger.info("Successfully authenticated with Qogita API")
            logger.info(f"Active cart QID: {self.cart_qid}")
            
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error during authentication: {e}")
            raise QogitaAPIError(f"Network error: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response during authentication: {e}")
            raise QogitaAPIError(f"Invalid API response: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during authentication: {e}")
            raise QogitaAPIError(f"Authentication error: {e}")
    
    def _ensure_authenticated(self) -> None:
        """Ensure we have a valid authentication token."""
        if not self.access_token:
            self.authenticate()
        elif self.token_expires_at and datetime.now() >= self.token_expires_at:
            logger.info("Token expired, re-authenticating...")
            self.authenticate()
    
    def _rate_limit_wait(self):
        """Implement basic rate limiting."""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.min_request_interval:
            wait_time = self.min_request_interval - time_since_last_request
            logger.debug(f"Rate limiting: waiting {wait_time:.2f} seconds")
            time.sleep(wait_time)
        
        self.last_request_time = time.time()
    
    def download_catalog(self, 
                        brand_name: Optional[str] = None,
                        category_name: Optional[str] = None,
                        stock_availability: Optional[str] = None,
                        page: int = 1,
                        size: int = 1000,
                        max_products: int = 2000) -> List[Dict[str, Any]]:
        """
        Download product catalog from Qogita using the CSV endpoint.
        
        Args:
            brand_name: Filter by specific brand name (exact match)
            category_name: Filter by category (e.g., 'fragrance')
            stock_availability: Filter by stock status (e.g., 'in_stock')
            page: Page number (default: 1)
            size: Products per page (default: 1000, max recommended)
            max_products: Maximum total products to return (default: 2000)
        
        Returns:
            List of product dictionaries
        """
        self._ensure_authenticated()
        self._rate_limit_wait()
        
        try:
            logger.info(f"Downloading catalog: brand='{brand_name}', category='{category_name}', stock='{stock_availability}'")
            
            # Build parameters
            params = {
                "page": page,
                "size": size
            }
            
            if brand_name:
                params["brand_name"] = brand_name
            if category_name:
                params["category_name"] = category_name
            if stock_availability:
                params["stock_availability"] = stock_availability
            
            # Make request to catalog download endpoint
            response = self.session.get(
                url=f"{self.base_url}/variants/search/download/",
                params=params
            )
            
            if response.status_code == 429:
                # Handle rate limiting
                error_data = response.json() if response.content else {}
                message = error_data.get("message", "Rate limited")
                
                # Extract retry-after from message if available
                retry_after = None
                if "seconds" in message:
                    try:
                        import re
                        match = re.search(r'(\d+)\s+seconds', message)
                        if match:
                            retry_after = int(match.group(1))
                    except:
                        pass
                
                raise QogitaRateLimitError(message, retry_after)
            
            elif response.status_code != 200:
                logger.error(f"Catalog download failed: {response.status_code} - {response.text}")
                raise QogitaAPIError(f"Catalog download failed: {response.status_code}")
            
            # Parse CSV content
            content = response.content.decode('utf-8')
            
            if not content.strip():
                logger.warning("Empty catalog response")
                return []
            
            products = self._parse_catalog_csv(content, max_products)
            
            logger.info(f"Successfully downloaded {len(products)} products from catalog")
            return products
            
        except QogitaRateLimitError:
            raise  # Re-raise rate limit errors
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error during catalog download: {e}")
            raise QogitaAPIError(f"Network error: {e}")
        except Exception as e:
            logger.error(f"Error downloading catalog: {e}")
            raise QogitaAPIError(f"Catalog download error: {e}")
    
    def _parse_catalog_csv(self, csv_content: str, max_products: int) -> List[Dict[str, Any]]:
        """
        Parse CSV catalog content into product dictionaries.
        
        Expected columns:
        GTIN, Name, Category, Brand, € Lowest Price inc. shipping, Unit, 
        Lowest Priced Offer Inventory, Has Extended Delivery Time, 
        Expected Delivery Time, Number of Offers, Total Inventory of All Offers, 
        Product URL, Image URL
        """
        products = []
        
        try:
            csv_reader = csv.reader(StringIO(csv_content))
            
            # Read headers
            headers = next(csv_reader)
            logger.debug(f"CSV headers: {headers}")
            
            # Expected column mapping
            column_mapping = {
                'GTIN': 'gtin',
                'Name': 'name', 
                'Category': 'category',
                'Brand': 'brand',
                '€ Lowest Price inc. shipping': 'price_eur',
                'Unit': 'unit',
                'Lowest Priced Offer Inventory': 'inventory',
                'Has Extended Delivery Time': 'extended_delivery',
                'Expected Delivery Time': 'delivery_time',
                'Number of Offers': 'offer_count',
                'Total Inventory of All Offers': 'total_inventory',
                'Product URL': 'product_url',
                'Image URL': 'image_url'
            }
            
            # Process rows
            for row_num, row in enumerate(csv_reader):
                if len(products) >= max_products:
                    logger.info(f"Reached max_products limit: {max_products}")
                    break
                
                if len(row) != len(headers):
                    logger.warning(f"Row {row_num + 2} has {len(row)} columns, expected {len(headers)}")
                    continue
                
                # Build product dictionary
                product = {}
                
                for i, header in enumerate(headers):
                    mapped_key = column_mapping.get(header, header.lower().replace(' ', '_'))
                    value = row[i].strip() if i < len(row) else ''
                    
                    # Type conversion for specific fields
                    if mapped_key == 'price_eur':
                        try:
                            product['wholesale_price'] = float(value) if value else 0.0
                            product['currency'] = 'EUR'
                        except ValueError:
                            product['wholesale_price'] = 0.0
                            product['currency'] = 'EUR'
                    elif mapped_key == 'inventory':
                        try:
                            product['stock_quantity'] = int(value) if value else 0
                        except ValueError:
                            product['stock_quantity'] = 0
                    elif mapped_key == 'offer_count':
                        try:
                            product['supplier_count'] = int(value) if value else 0
                        except ValueError:
                            product['supplier_count'] = 0
                    elif mapped_key == 'total_inventory':
                        try:
                            product['total_stock'] = int(value) if value else 0
                        except ValueError:
                            product['total_stock'] = 0
                    elif mapped_key == 'extended_delivery':
                        product['has_extended_delivery'] = value.lower() in ['yes', 'true', '1']
                    else:
                        product[mapped_key] = value
                
                # Add computed fields
                product['source'] = 'qogita'
                product['qogita_id'] = product.get('gtin', f"qogita_{row_num}")
                
                # Ensure required fields exist
                if not product.get('gtin'):
                    logger.warning(f"Product on row {row_num + 2} missing GTIN, skipping")
                    continue
                
                if not product.get('name'):
                    logger.warning(f"Product on row {row_num + 2} missing name, skipping")
                    continue
                
                products.append(product)
            
            logger.info(f"Parsed {len(products)} valid products from CSV")
            
        except csv.Error as e:
            logger.error(f"CSV parsing error: {e}")
            raise QogitaAPIError(f"CSV parsing error: {e}")
        except Exception as e:
            logger.error(f"Error parsing catalog CSV: {e}")
            raise QogitaAPIError(f"CSV processing error: {e}")
        
        return products
    
    def search_products_by_brand(self, brand_name: str, limit: int = 2000) -> List[Dict[str, Any]]:
        """
        Search for products by exact brand name using catalog download.
        
        Args:
            brand_name: Exact brand name to search for
            limit: Maximum number of products to return (default: 2000)
        
        Returns:
            List of product dictionaries with product information
        """
        try:
            logger.info(f"Searching for products from brand: {brand_name}")
            
            products = self.download_catalog(
                brand_name=brand_name,
                max_products=limit
            )
            
            logger.info(f"Found {len(products)} products for brand '{brand_name}'")
            return products
            
        except QogitaRateLimitError as e:
            logger.error(f"Rate limited while searching brand '{brand_name}': {e}")
            if e.retry_after:
                logger.info(f"Retry after {e.retry_after} seconds")
            raise
        except Exception as e:
            logger.error(f"Error searching products by brand: {e}")
            raise QogitaAPIError(f"Product search error: {e}")
    
    def get_available_categories(self) -> List[str]:
        """Get list of available product categories."""
        # Based on our testing, known working categories
        return [
            "fragrance",
            # Add more as we discover them
        ]
    
    def search_by_category(self, category_name: str, limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Search products by category.
        
        Args:
            category_name: Category name (e.g., 'fragrance')
            limit: Maximum products to return
            
        Returns:
            List of product dictionaries
        """
        try:
            logger.info(f"Searching products in category: {category_name}")
            
            products = self.download_catalog(
                category_name=category_name,
                max_products=limit
            )
            
            logger.info(f"Found {len(products)} products in category '{category_name}'")
            return products
            
        except Exception as e:
            logger.error(f"Error searching by category: {e}")
            raise QogitaAPIError(f"Category search error: {e}")
    
    def test_connection(self) -> bool:
        """Test the API connection and authentication."""
        try:
            success = self.authenticate()
            if success:
                # Try a small catalog request to verify full access
                try:
                    test_products = self.download_catalog(size=1, max_products=1)
                    logger.info(f"Connection test successful - can access catalog with {len(test_products)} test products")
                    return True
                except QogitaRateLimitError:
                    logger.warning("Connection test hit rate limit but authentication works")
                    return True
                except Exception as e:
                    logger.warning(f"Catalog access limited but authentication works: {e}")
                    return True
            return False
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False


def create_qogita_client(email: str, password: str) -> QogitaAPI:
    """Factory function to create a Qogita API client."""
    return QogitaAPI(email, password)
