"""
Product Matcher - Match Qogita wholesale products with Amazon data

This module handles the matching between Qogita wholesale products (identified by GTIN)
and Amazon products via Keepa API for bulk profitability analysis.
"""

import logging
import re
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from PyQt6.QtCore import QObject, pyqtSignal

from core.keepa_api import KeepaAPI
from core.enhanced_roi_calculator import EnhancedROICalculator
from utils.enhanced_gtin_processor import EnhancedGTINProcessor, QogitaGTINAnalyzer


@dataclass
class QogitaProduct:
    """Data class for Qogita product information"""
    gtin: str
    name: str
    category: str
    brand: str
    wholesale_price: float
    unit: str
    stock: int
    suppliers: int
    product_url: str
    image_url: str


@dataclass
class MatchedProduct:
    """Data class for matched product with Amazon data"""
    qogita_product: QogitaProduct
    amazon_asin: Optional[str] = None
    amazon_price: Optional[float] = None
    amazon_url: Optional[str] = None
    keepa_data: Optional[Dict] = None
    profit_margin: Optional[float] = None
    roi_percentage: Optional[float] = None
    match_status: str = "pending"  # pending, matched, matched_by_name, not_found, error, gtin_invalid, no_price
    match_confidence: int = 0  # 0-100, confidence in the match
    gtin_analysis: Optional[Dict] = None  # GTIN processing results
    search_attempts: List[str] = None  # GTINs that were tried


class ProductMatcher(QObject):
    """
    Matches Qogita products with Amazon data for profitability analysis
    """
    
    # Signals for progress tracking
    progress_updated = pyqtSignal(int, int, str)  # current, total, status
    product_matched = pyqtSignal(object)  # MatchedProduct
    matching_completed = pyqtSignal(list)  # List of MatchedProduct
    error_occurred = pyqtSignal(str)
    
    def __init__(self, keepa_api: KeepaAPI, calculator: EnhancedROICalculator):
        super().__init__()
        self.keepa_api = keepa_api
        self.calculator = calculator
        self.logger = logging.getLogger(__name__)
        
        # Enhanced GTIN processing
        self.gtin_processor = EnhancedGTINProcessor()
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 1.2  # Seconds between Keepa requests
        
    def match_products_bulk(self, qogita_products: List[QogitaProduct]) -> List[MatchedProduct]:
        """
        Match a list of Qogita products with Amazon data
        
        Args:
            qogita_products: List of QogitaProduct objects
            
        Returns:
            List of MatchedProduct objects with matching results
        """
        matched_products = []
        total_products = len(qogita_products)
        
        self.logger.info(f"Starting bulk matching for {total_products} products")
        
        try:
            for i, qogita_product in enumerate(qogita_products):
                # Update progress
                self.progress_updated.emit(i + 1, total_products, f"Matching {qogita_product.name}")
                
                # Match individual product
                matched_product = self.match_single_product(qogita_product)
                matched_products.append(matched_product)
                
                # Emit individual result
                self.product_matched.emit(matched_product)
                
                # Rate limiting for Keepa API
                self._enforce_rate_limit()
                
            self.logger.info(f"Completed bulk matching. Results: {len(matched_products)} processed")
            self.matching_completed.emit(matched_products)
            
        except Exception as e:
            error_msg = f"Error during bulk matching: {str(e)}"
            self.logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            
        return matched_products
    
    def match_single_product(self, qogita_product: QogitaProduct) -> MatchedProduct:
        """
        Match a single Qogita product with Amazon data using enhanced GTIN processing
        
        Args:
            qogita_product: QogitaProduct to match
            
        Returns:
            MatchedProduct with matching results
        """
        matched_product = MatchedProduct(
            qogita_product=qogita_product,
            search_attempts=[]
        )
        
        try:
            # Step 1: Process and validate GTIN
            gtin_result = self.gtin_processor.process_gtin(qogita_product.gtin)
            matched_product.gtin_analysis = gtin_result
            
            if not gtin_result['is_valid']:
                matched_product.match_status = "gtin_invalid"
                matched_product.match_confidence = 0
                self.logger.debug(f"Invalid GTIN for product: {qogita_product.gtin}")
                return matched_product
            
            # Step 2: Get best GTIN for Amazon search
            best_gtin = self.gtin_processor.find_best_gtin_for_amazon(gtin_result)
            if not best_gtin:
                matched_product.match_status = "gtin_invalid"
                return matched_product
            
            # Step 3: Try searching with GTIN variants
            search_variants = gtin_result.get('search_variants', [best_gtin])
            
            # Ensure best GTIN is first in the list
            if best_gtin not in search_variants:
                search_variants.insert(0, best_gtin)
            elif search_variants[0] != best_gtin:
                search_variants.remove(best_gtin)
                search_variants.insert(0, best_gtin)
            
            keepa_result = None
            successful_gtin = None
            
            for gtin_variant in search_variants:
                matched_product.search_attempts.append(gtin_variant)
                self.logger.debug(f"Trying GTIN variant: {gtin_variant}")
                
                # Try this GTIN variant
                keepa_result = self._search_by_gtin(gtin_variant)
                
                if keepa_result and keepa_result.get('success', True) != False:
                    successful_gtin = gtin_variant
                    self.logger.debug(f"Found match with GTIN: {gtin_variant}")
                    break
                
                # Rate limiting between attempts
                self._enforce_rate_limit()
            
            # Step 4: Process results
            if keepa_result and successful_gtin:
                matched_product.keepa_data = keepa_result
                matched_product.amazon_asin = keepa_result.get('asin')
                
                if matched_product.amazon_asin:
                    matched_product.amazon_url = f"https://www.amazon.fr/dp/{matched_product.amazon_asin}"
                
                # Extract current Amazon price
                amazon_price = self._extract_amazon_price(keepa_result)
                if amazon_price:
                    matched_product.amazon_price = amazon_price
                    
                    # Calculate profitability
                    profit_analysis = self._calculate_profitability(
                        qogita_product.wholesale_price,
                        amazon_price,
                        keepa_result
                    )
                    
                    matched_product.profit_margin = profit_analysis.get('profit_margin')
                    matched_product.roi_percentage = profit_analysis.get('roi_percentage')
                    matched_product.match_status = "matched"
                    
                    # Set confidence based on GTIN confidence and exact match
                    base_confidence = gtin_result['confidence']
                    if successful_gtin == gtin_result['normalized']:
                        matched_product.match_confidence = base_confidence
                    else:
                        # Slightly lower confidence for variant matches
                        matched_product.match_confidence = max(70, base_confidence - 10)
                    
                    self.logger.debug(f"Successfully matched {qogita_product.gtin} -> {matched_product.amazon_asin} (confidence: {matched_product.match_confidence}%)")
                else:
                    matched_product.match_status = "no_price"
                    matched_product.match_confidence = 60  # Found product but no price
                    self.logger.debug(f"Found ASIN for {qogita_product.gtin} but no current price")
            else:
                # Step 5: Fallback to brand + name search if GTIN failed
                self.logger.debug(f"GTIN search failed for {qogita_product.gtin}, trying brand+name fallback")
                fallback_result = self._search_by_brand_and_name(qogita_product)
                
                if fallback_result:
                    matched_product.keepa_data = fallback_result
                    matched_product.amazon_asin = fallback_result.get('asin')
                    
                    if matched_product.amazon_asin:
                        matched_product.amazon_url = f"https://www.amazon.fr/dp/{matched_product.amazon_asin}"
                    
                    # Extract current Amazon price
                    amazon_price = self._extract_amazon_price(fallback_result)
                    if amazon_price:
                        matched_product.amazon_price = amazon_price
                        
                        # Calculate profitability
                        profit_analysis = self._calculate_profitability(
                            qogita_product.wholesale_price,
                            amazon_price,
                            fallback_result
                        )
                        
                        matched_product.profit_margin = profit_analysis.get('profit_margin')
                        matched_product.roi_percentage = profit_analysis.get('roi_percentage')
                        matched_product.match_status = "matched_by_name"
                        # Lower confidence for name-based matches
                        matched_product.match_confidence = 60
                        
                        self.logger.debug(f"Fallback match found: {qogita_product.brand} {qogita_product.name} -> {matched_product.amazon_asin}")
                    else:
                        matched_product.match_status = "no_price"
                        matched_product.match_confidence = 40
                        
                else:
                    matched_product.match_status = "not_found"
                    matched_product.match_confidence = 0
                    self.logger.debug(f"No Amazon match found for GTIN: {qogita_product.gtin}")
                
        except Exception as e:
            matched_product.match_status = "error"
            matched_product.match_confidence = 0
            self.logger.error(f"Error matching product {qogita_product.gtin}: {str(e)}")
            
        return matched_product
    
    def _search_by_gtin(self, gtin: str) -> Optional[Dict]:
        """
        Search Amazon/Keepa for product by GTIN/EAN
        
        Args:
            gtin: GTIN/EAN code to search for
            
        Returns:
            Keepa product data if found, None otherwise
        """
        try:
            # Use Keepa's product lookup by GTIN/EAN/UPC
            product_data = self.keepa_api.get_product_data(gtin, domain=4)  # 4 = France
            
            if product_data and product_data.get('success', True) != False:
                return product_data
                
        except Exception as e:
            self.logger.error(f"Error searching for GTIN {gtin}: {str(e)}")
            
        return None
    
    def _search_by_brand_and_name(self, qogita_product: QogitaProduct) -> Optional[Dict]:
        """
        Fallback search by brand and product name when GTIN search fails
        
        Args:
            qogita_product: QogitaProduct to search for
            
        Returns:
            Keepa product data if found, None otherwise
        """
        try:
            # Create search queries with different combinations
            search_queries = self._generate_name_search_queries(qogita_product)
            
            for query in search_queries:
                self.logger.debug(f"Trying search query: {query}")
                
                try:
                    # Use Keepa's search functionality
                    search_results = self.keepa_api.search_products(query, domain='fr')
                    
                    if search_results and isinstance(search_results, list) and len(search_results) > 0:
                        # Take the first result as best match
                        # In a more sophisticated implementation, we could score results
                        best_match = search_results[0]
                        
                        # Get detailed product data
                        if 'asin' in best_match:
                            product_data = self.keepa_api.get_product_data(best_match['asin'], domain=4)  # 4 = France
                            if product_data:
                                return product_data
                                
                except Exception as search_error:
                    self.logger.warning(f"Search query '{query}' failed: {str(search_error)}")
                    continue
                
                # Rate limiting between search attempts
                self._enforce_rate_limit()
                
        except Exception as e:
            self.logger.error(f"Error in brand+name search for {qogita_product.brand} {qogita_product.name}: {str(e)}")
            
        return None
    
    def _generate_name_search_queries(self, qogita_product: QogitaProduct) -> List[str]:
        """
        Generate search query variations for brand and name fallback search
        
        Args:
            qogita_product: QogitaProduct to generate queries for
            
        Returns:
            List of search queries ordered by likelihood of success
        """
        queries = []
        brand = qogita_product.brand.strip()
        name = qogita_product.name.strip()
        
        # Clean common suffixes/prefixes
        name_cleaned = self._clean_product_name(name)
        
        # Priority order: most specific to least specific
        queries = [
            f"{brand} {name_cleaned}",  # Full brand + cleaned name
            f"{brand} {name}",  # Full brand + original name
            name_cleaned,  # Just cleaned name
            name,  # Just original name
        ]
        
        # Remove duplicates while preserving order
        seen = set()
        unique_queries = []
        for query in queries:
            if query and query.lower() not in seen:
                seen.add(query.lower())
                unique_queries.append(query)
                
        return unique_queries
    
    def _clean_product_name(self, name: str) -> str:
        """
        Clean product name for better search results
        
        Args:
            name: Original product name
            
        Returns:
            Cleaned product name
        """
        # Remove common e-commerce suffixes
        suffixes_to_remove = [
            r'\d+ml\b', r'\d+g\b', r'\d+oz\b',  # Volume/weight
            r'\d+x\d+', r'\d+pk\b', r'\d+ pack\b',  # Package info
            r'\- \w+$',  # Trailing descriptors after dash
        ]
        
        cleaned = name
        for suffix_pattern in suffixes_to_remove:
            cleaned = re.sub(suffix_pattern, '', cleaned, flags=re.IGNORECASE)
        
        # Remove extra whitespace
        cleaned = ' '.join(cleaned.split())
        
        return cleaned.strip()
    
    def _extract_amazon_price(self, keepa_data: Dict) -> Optional[float]:
        """
        Extract current Amazon price from Keepa data
        
        Args:
            keepa_data: Keepa product data
            
        Returns:
            Current Amazon price in EUR, or None if not available
        """
        try:
            # Try to get FBA price first (more accurate for sellers)
            if 'data' in keepa_data and 'csv' in keepa_data['data']:
                csv_data = keepa_data['data']['csv']
                
                # FBA price (index 16)
                if 16 in csv_data and csv_data[16]:
                    fba_prices = csv_data[16]
                    if len(fba_prices) >= 2:
                        latest_fba_price = fba_prices[-1]
                        if latest_fba_price > 0:
                            return latest_fba_price / 100  # Convert from Keepa format
                
                # Amazon price (index 0)
                if 0 in csv_data and csv_data[0]:
                    amazon_prices = csv_data[0]
                    if len(amazon_prices) >= 2:
                        latest_amazon_price = amazon_prices[-1]
                        if latest_amazon_price > 0:
                            return latest_amazon_price / 100  # Convert from Keepa format
            
            # Fallback to stats
            if 'stats' in keepa_data:
                stats = keepa_data['stats']
                if 'current' in stats and stats['current'][0] > 0:
                    return stats['current'][0] / 100
                    
        except Exception as e:
            self.logger.error(f"Error extracting price from Keepa data: {str(e)}")
            
        return None
    
    def _calculate_profitability(self, wholesale_price: float, amazon_price: float, keepa_data: Dict) -> Dict:
        """
        Calculate profitability metrics
        
        Args:
            wholesale_price: Qogita wholesale price in EUR
            amazon_price: Amazon selling price in EUR
            keepa_data: Keepa product data for additional calculations
            
        Returns:
            Dictionary with profit_margin and roi_percentage
        """
        try:
            # Use the enhanced calculator for comprehensive fee calculation
            # For now, use basic calculation - can be enhanced with product specifics
            
            # Estimate Amazon fees (approximately 15% + €1 for cosmetics)
            amazon_fee_rate = 0.15
            amazon_fixed_fee = 1.0
            estimated_fees = (amazon_price * amazon_fee_rate) + amazon_fixed_fee
            
            # Calculate profit
            profit_margin = amazon_price - wholesale_price - estimated_fees
            roi_percentage = (profit_margin / wholesale_price) * 100 if wholesale_price > 0 else 0
            
            return {
                'profit_margin': profit_margin,
                'roi_percentage': roi_percentage,
                'estimated_fees': estimated_fees
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating profitability: {str(e)}")
            return {'profit_margin': 0, 'roi_percentage': 0}
    
    def _enforce_rate_limit(self):
        """Enforce rate limiting for API requests"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last_request
            time.sleep(sleep_time)
            
        self.last_request_time = time.time()
    
    def analyze_brand_gtin_quality(self, qogita_products: List[QogitaProduct]) -> Dict:
        """
        Analyze GTIN quality across a brand's products to predict matching success
        
        Args:
            qogita_products: List of QogitaProduct objects
            
        Returns:
            Analysis results with statistics and recommendations
        """
        # Convert to format expected by analyzer
        products_for_analysis = []
        for product in qogita_products:
            products_for_analysis.append({
                'gtin': product.gtin,
                'name': product.name,
                'brand': product.brand,
                'wholesale_price': product.wholesale_price
            })
        
        analyzer = QogitaGTINAnalyzer()
        return analyzer.analyze_brand_gtins(products_for_analysis)
    
    def filter_profitable_products(self, matched_products: List[MatchedProduct], 
                                 min_roi: float = 15.0, min_price: float = 10.0) -> List[MatchedProduct]:
        """
        Filter products based on profitability criteria
        
        Args:
            matched_products: List of MatchedProduct objects
            min_roi: Minimum ROI percentage
            min_price: Minimum Amazon price in EUR
            
        Returns:
            Filtered list of profitable products
        """
        profitable_products = []
        
        for product in matched_products:
            if (product.match_status == "matched" and 
                product.roi_percentage is not None and 
                product.amazon_price is not None):
                
                if (product.roi_percentage >= min_roi and 
                    product.amazon_price >= min_price):
                    profitable_products.append(product)
        
        self.logger.info(f"Filtered {len(profitable_products)} profitable products from {len(matched_products)} total")
        return profitable_products


# Utility functions for CSV export
def export_matched_products_to_csv(matched_products: List[MatchedProduct], filepath: str):
    """Export matched products to CSV file with enhanced data"""
    import csv
    
    with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'GTIN', 'Brand', 'Product_Name', 'Category', 'Wholesale_Price_EUR',
            'Amazon_Price_EUR', 'Profit_Margin_EUR', 'ROI_Percentage', 'Match_Status',
            'Match_Confidence', 'Amazon_ASIN', 'Amazon_URL', 'Qogita_URL', 'Stock', 'Suppliers',
            'GTIN_Format', 'GTIN_Valid', 'Search_Attempts'
        ]
        
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for product in matched_products:
            qp = product.qogita_product
            gtin_analysis = product.gtin_analysis or {}
            
            writer.writerow({
                'GTIN': qp.gtin,
                'Brand': qp.brand,
                'Product_Name': qp.name,
                'Category': qp.category,
                'Wholesale_Price_EUR': qp.wholesale_price,
                'Amazon_Price_EUR': product.amazon_price or 'N/A',
                'Profit_Margin_EUR': product.profit_margin or 'N/A',
                'ROI_Percentage': product.roi_percentage or 'N/A',
                'Match_Status': product.match_status,
                'Match_Confidence': f"{product.match_confidence}%",
                'Amazon_ASIN': product.amazon_asin or 'N/A',
                'Amazon_URL': product.amazon_url or 'N/A',
                'Qogita_URL': qp.product_url,
                'Stock': qp.stock,
                'Suppliers': qp.suppliers,
                'GTIN_Format': gtin_analysis.get('format', 'Unknown'),
                'GTIN_Valid': 'Yes' if gtin_analysis.get('is_valid') else 'No',
                'Search_Attempts': ', '.join(product.search_attempts or [])
            })
