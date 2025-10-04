"""
Column Detector - Intelligent column purpose detection with fuzzy matching

Auto-detects the purpose of columns in wholesaler catalogs using:
- Fuzzy string matching (Levenshtein distance)
- Pattern recognition (GTINs, prices, numeric fields)
- Semantic similarity
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


@dataclass
class ColumnMapping:
    """Mapping between catalog column and standard field"""
    catalog_column: str
    standard_field: str
    confidence: float  # 0.0 to 1.0
    detection_method: str  # 'exact', 'fuzzy', 'pattern'


@dataclass
class DetectionResult:
    """Result of column detection"""
    mappings: List[ColumnMapping]
    unmapped_columns: List[str]
    confidence_score: float  # Overall confidence
    warnings: List[str]


class ColumnDetector:
    """
    Intelligent detector for column purposes in catalog files.
    
    Detects:
    - Product identifiers (GTIN, EAN, UPC, ASIN, SKU)
    - Prices (wholesale, retail, with various formats)
    - Stock/quantity fields
    - Product information (name, brand, category)
    - Additional metadata
    """
    
    # Standard field definitions with alternative names
    FIELD_PATTERNS = {
        'gtin': {
            'keywords': ['gtin', 'ean', 'upc', 'barcode', 'ean13', 'ean-13', 'product code', 'article number'],
            'pattern': r'^\d{8,14}$',  # 8-14 digit code
            'priority': 10
        },
        'asin': {
            'keywords': ['asin', 'amazon', 'amazon id'],
            'pattern': r'^B[0-9A-Z]{9}$',  # Amazon ASIN format
            'priority': 9
        },
        'sku': {
            'keywords': ['sku', 'product id', 'item id', 'article id', 'reference', 'ref'],
            'pattern': r'^[A-Z0-9\-]+$',
            'priority': 8
        },
        'product_name': {
            'keywords': ['name', 'title', 'product name', 'product title', 'description', 'item name'],
            'pattern': None,
            'priority': 7
        },
        'brand': {
            'keywords': ['brand', 'manufacturer', 'make', 'supplier'],
            'pattern': None,
            'priority': 6
        },
        'category': {
            'keywords': ['category', 'type', 'department', 'class', 'group'],
            'pattern': None,
            'priority': 5
        },
        'wholesale_price': {
            'keywords': ['price', 'wholesale', 'cost', 'unit price', 'buy price', 'purchase price', 'net price'],
            'pattern': r'[\d.,]+',  # Numeric with decimal
            'priority': 9
        },
        'retail_price': {
            'keywords': ['retail', 'rrp', 'msrp', 'recommended', 'sell price', 'list price'],
            'pattern': r'[\d.,]+',
            'priority': 4
        },
        'stock': {
            'keywords': ['stock', 'quantity', 'qty', 'available', 'inventory', 'in stock', 'units'],
            'pattern': r'^\d+$',  # Integer
            'priority': 6
        },
        'moq': {
            'keywords': ['moq', 'minimum', 'min order', 'minimum quantity', 'min qty'],
            'pattern': r'^\d+$',
            'priority': 3
        },
        'weight': {
            'keywords': ['weight', 'kg', 'grams', 'mass'],
            'pattern': r'[\d.,]+',
            'priority': 2
        },
        'dimensions': {
            'keywords': ['size', 'dimensions', 'length', 'width', 'height', 'dim'],
            'pattern': None,
            'priority': 2
        }
    }
    
    def __init__(self, min_confidence: float = 0.6):
        """
        Initialize detector.
        
        Args:
            min_confidence: Minimum confidence score to accept mapping (0.0 to 1.0)
        """
        self.min_confidence = min_confidence
        self.logger = logging.getLogger(__name__)
    
    def detect_columns(self, headers: List[str], sample_rows: List[Dict[str, str]]) -> DetectionResult:
        """
        Detect column purposes from headers and sample data.
        
        Args:
            headers: List of column headers
            sample_rows: Sample data rows for pattern matching
            
        Returns:
            DetectionResult with mappings and confidence
        """
        mappings = []
        used_fields = set()
        warnings = []
        
        # First pass: Exact and fuzzy matching on headers
        for header in headers:
            best_match = self._match_header(header, used_fields)
            if best_match:
                mappings.append(best_match)
                used_fields.add(best_match.standard_field)
        
        # Second pass: Pattern matching on sample data for unmapped columns
        unmapped_headers = [h for h in headers if h not in [m.catalog_column for m in mappings]]
        
        if sample_rows and unmapped_headers:
            pattern_mappings = self._match_by_pattern(unmapped_headers, sample_rows, used_fields)
            mappings.extend(pattern_mappings)
            for pm in pattern_mappings:
                used_fields.add(pm.standard_field)
        
        # Calculate overall confidence
        if mappings:
            confidence_score = sum(m.confidence for m in mappings) / len(mappings)
        else:
            confidence_score = 0.0
        
        # Find unmapped columns
        mapped_columns = {m.catalog_column for m in mappings}
        unmapped_columns = [h for h in headers if h not in mapped_columns]
        
        # Generate warnings
        critical_fields = ['gtin', 'wholesale_price', 'product_name']
        missing_critical = [f for f in critical_fields if f not in used_fields]
        
        if missing_critical:
            warnings.append(f"Missing critical fields: {', '.join(missing_critical)}")
        
        if len(unmapped_columns) > len(headers) * 0.5:
            warnings.append(f"{len(unmapped_columns)} columns could not be mapped")
        
        # Sort mappings by confidence (highest first)
        mappings.sort(key=lambda m: m.confidence, reverse=True)
        
        self.logger.info(f"Detected {len(mappings)} column mappings with {confidence_score:.2f} confidence")
        
        return DetectionResult(
            mappings=mappings,
            unmapped_columns=unmapped_columns,
            confidence_score=confidence_score,
            warnings=warnings
        )
    
    def _match_header(self, header: str, used_fields: Set[str]) -> Optional[ColumnMapping]:
        """
        Match header using exact and fuzzy string matching.
        
        Args:
            header: Column header to match
            used_fields: Set of already mapped standard fields
            
        Returns:
            ColumnMapping if match found, None otherwise
        """
        header_lower = header.lower().strip()
        
        best_match = None
        best_score = 0.0
        best_field = None
        
        for field, config in self.FIELD_PATTERNS.items():
            # Skip if field already mapped
            if field in used_fields:
                continue
            
            keywords = config['keywords']
            priority = config['priority']
            
            # Check exact match
            if header_lower in keywords:
                return ColumnMapping(
                    catalog_column=header,
                    standard_field=field,
                    confidence=1.0,
                    detection_method='exact'
                )
            
            # Check fuzzy match
            for keyword in keywords:
                similarity = self._string_similarity(header_lower, keyword)
                
                # Boost score by priority
                adjusted_score = similarity * (1 + priority * 0.05)
                
                if adjusted_score > best_score:
                    best_score = adjusted_score
                    best_field = field
                    best_match = keyword
        
        # Return best fuzzy match if above threshold
        if best_score >= self.min_confidence:
            return ColumnMapping(
                catalog_column=header,
                standard_field=best_field,
                confidence=min(best_score, 1.0),
                detection_method='fuzzy'
            )
        
        return None
    
    def _match_by_pattern(self, headers: List[str], sample_rows: List[Dict[str, str]], 
                          used_fields: Set[str]) -> List[ColumnMapping]:
        """
        Match columns by analyzing data patterns in sample rows.
        
        Args:
            headers: Unmapped headers
            sample_rows: Sample data rows
            used_fields: Already mapped fields
            
        Returns:
            List of ColumnMapping objects
        """
        mappings = []
        
        for header in headers:
            # Extract sample values for this column
            sample_values = [row.get(header, '').strip() for row in sample_rows[:20]]
            sample_values = [v for v in sample_values if v]  # Remove empty
            
            if not sample_values:
                continue
            
            # Try to match patterns
            best_match = self._analyze_pattern(header, sample_values, used_fields)
            
            if best_match:
                mappings.append(best_match)
                used_fields.add(best_match.standard_field)
        
        return mappings
    
    def _analyze_pattern(self, header: str, values: List[str], 
                        used_fields: Set[str]) -> Optional[ColumnMapping]:
        """
        Analyze data pattern to determine field type.
        
        Args:
            header: Column header
            values: Sample values from column
            used_fields: Already mapped fields
            
        Returns:
            ColumnMapping if pattern matched, None otherwise
        """
        if not values:
            return None
        
        # Check each field pattern
        for field, config in self.FIELD_PATTERNS.items():
            if field in used_fields:
                continue
            
            pattern = config.get('pattern')
            if not pattern:
                continue
            
            # Check how many values match the pattern
            matches = sum(1 for v in values if re.match(pattern, v.replace(' ', '')))
            match_ratio = matches / len(values)
            
            # Require high match ratio for pattern detection
            if match_ratio >= 0.7:
                confidence = min(0.85, match_ratio)  # Cap pattern confidence at 0.85
                
                return ColumnMapping(
                    catalog_column=header,
                    standard_field=field,
                    confidence=confidence,
                    detection_method='pattern'
                )
        
        return None
    
    def _string_similarity(self, s1: str, s2: str) -> float:
        """
        Calculate similarity between two strings using SequenceMatcher.
        
        Returns:
            Similarity score from 0.0 to 1.0
        """
        # Also check if one string contains the other
        if s1 in s2 or s2 in s1:
            return 0.9
        
        return SequenceMatcher(None, s1, s2).ratio()
    
    def suggest_mapping(self, unmapped_column: str, available_fields: List[str]) -> List[Tuple[str, float]]:
        """
        Suggest possible mappings for an unmapped column.
        
        Args:
            unmapped_column: Column that needs mapping
            available_fields: List of available standard fields
            
        Returns:
            List of (field, confidence) tuples, sorted by confidence
        """
        suggestions = []
        
        col_lower = unmapped_column.lower().strip()
        
        for field in available_fields:
            if field not in self.FIELD_PATTERNS:
                continue
            
            keywords = self.FIELD_PATTERNS[field]['keywords']
            
            # Calculate best similarity score
            best_similarity = max(self._string_similarity(col_lower, kw) for kw in keywords)
            
            if best_similarity >= 0.4:  # Lower threshold for suggestions
                suggestions.append((field, best_similarity))
        
        # Sort by confidence (highest first)
        suggestions.sort(key=lambda x: x[1], reverse=True)
        
        return suggestions[:5]  # Return top 5 suggestions
    
    def validate_mapping(self, mapping: ColumnMapping, sample_rows: List[Dict[str, str]]) -> Dict[str, any]:
        """
        Validate a mapping against sample data.
        
        Args:
            mapping: Column mapping to validate
            sample_rows: Sample data rows
            
        Returns:
            Validation result with statistics
        """
        result = {
            'is_valid': True,
            'warnings': [],
            'stats': {}
        }
        
        # Extract values for this column
        values = [row.get(mapping.catalog_column, '').strip() for row in sample_rows]
        non_empty = [v for v in values if v]
        
        result['stats']['total_values'] = len(values)
        result['stats']['non_empty_values'] = len(non_empty)
        result['stats']['empty_ratio'] = (len(values) - len(non_empty)) / len(values) if values else 0
        
        # Check pattern match if applicable
        field_config = self.FIELD_PATTERNS.get(mapping.standard_field)
        if field_config and field_config.get('pattern'):
            pattern = field_config['pattern']
            matches = sum(1 for v in non_empty if re.match(pattern, v.replace(' ', '')))
            match_ratio = matches / len(non_empty) if non_empty else 0
            result['stats']['pattern_match_ratio'] = match_ratio
            
            if match_ratio < 0.5:
                result['warnings'].append(
                    f"Only {match_ratio:.1%} of values match expected pattern for {mapping.standard_field}"
                )
        
        # Warn about high empty ratio
        if result['stats']['empty_ratio'] > 0.3:
            result['warnings'].append(
                f"{result['stats']['empty_ratio']:.1%} of values are empty"
            )
        
        return result
