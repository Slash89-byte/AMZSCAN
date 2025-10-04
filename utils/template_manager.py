"""
Template Manager - Save and load column mappings for known wholesalers

Features:
- Store successful column mappings per wholesaler
- Auto-detect wholesaler from file metadata
- Template versioning and updates
- Import/export templates
"""

import json
import logging
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class WholesalerTemplate:
    """Template for a specific wholesaler's catalog format"""
    name: str
    column_mappings: Dict[str, str]  # catalog_column -> standard_field
    currency: str
    vat_included: bool
    metadata: Dict[str, Any]
    created_date: str
    last_used_date: str
    use_count: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WholesalerTemplate':
        """Create from dictionary"""
        return cls(**data)


class TemplateManager:
    """
    Manages wholesaler catalog templates.
    
    Features:
    - Save/load templates to/from JSON
    - Auto-detect matching templates
    - Template suggestions based on similarity
    - Usage statistics tracking
    """
    
    def __init__(self, templates_dir: str = None):
        """
        Initialize template manager.
        
        Args:
            templates_dir: Directory to store templates (default: ./templates)
        """
        if templates_dir is None:
            templates_dir = Path(__file__).parent.parent / 'templates'
        
        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(exist_ok=True)
        
        self.templates_file = self.templates_dir / 'wholesaler_templates.json'
        self.logger = logging.getLogger(__name__)
        
        # Load existing templates
        self.templates: Dict[str, WholesalerTemplate] = self._load_templates()
    
    def _load_templates(self) -> Dict[str, WholesalerTemplate]:
        """Load templates from JSON file"""
        if not self.templates_file.exists():
            self.logger.info("No existing templates found, starting fresh")
            return {}
        
        try:
            with open(self.templates_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            templates = {}
            for name, template_data in data.items():
                try:
                    templates[name] = WholesalerTemplate.from_dict(template_data)
                except Exception as e:
                    self.logger.error(f"Error loading template '{name}': {str(e)}")
            
            self.logger.info(f"Loaded {len(templates)} templates")
            return templates
            
        except Exception as e:
            self.logger.error(f"Error loading templates file: {str(e)}")
            return {}
    
    def _save_templates(self):
        """Save templates to JSON file"""
        try:
            data = {name: template.to_dict() for name, template in self.templates.items()}
            
            with open(self.templates_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Saved {len(self.templates)} templates")
            
        except Exception as e:
            self.logger.error(f"Error saving templates: {str(e)}")
    
    def save_template(self, name: str, column_mappings: Dict[str, str], 
                     currency: str, vat_included: bool, 
                     metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Save a new template or update existing one.
        
        Args:
            name: Template name (usually wholesaler name)
            column_mappings: Dictionary of catalog_column -> standard_field
            currency: Currency code (EUR, USD, GBP, etc.)
            vat_included: Whether prices include VAT
            metadata: Additional metadata (file format, delimiter, etc.)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Normalize name
            name = name.strip()
            
            if not name:
                self.logger.error("Template name cannot be empty")
                return False
            
            if not column_mappings:
                self.logger.error("Column mappings cannot be empty")
                return False
            
            # Check if template exists
            if name in self.templates:
                # Update existing template
                template = self.templates[name]
                template.column_mappings = column_mappings
                template.currency = currency
                template.vat_included = vat_included
                template.metadata.update(metadata or {})
                template.last_used_date = datetime.now().isoformat()
                template.use_count += 1
                self.logger.info(f"Updated existing template: {name}")
            else:
                # Create new template
                template = WholesalerTemplate(
                    name=name,
                    column_mappings=column_mappings,
                    currency=currency,
                    vat_included=vat_included,
                    metadata=metadata or {},
                    created_date=datetime.now().isoformat(),
                    last_used_date=datetime.now().isoformat(),
                    use_count=1
                )
                self.templates[name] = template
                self.logger.info(f"Created new template: {name}")
            
            # Save to file
            self._save_templates()
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving template: {str(e)}")
            return False
    
    def get_template(self, name: str) -> Optional[WholesalerTemplate]:
        """
        Get template by name.
        
        Args:
            name: Template name
            
        Returns:
            WholesalerTemplate or None if not found
        """
        template = self.templates.get(name)
        
        if template:
            # Update usage statistics
            template.last_used_date = datetime.now().isoformat()
            template.use_count += 1
            self._save_templates()
        
        return template
    
    def list_templates(self) -> List[Dict[str, Any]]:
        """
        List all available templates with metadata.
        
        Returns:
            List of template summaries
        """
        summaries = []
        
        for name, template in self.templates.items():
            summaries.append({
                'name': name,
                'currency': template.currency,
                'vat_included': template.vat_included,
                'column_count': len(template.column_mappings),
                'created_date': template.created_date,
                'last_used_date': template.last_used_date,
                'use_count': template.use_count
            })
        
        # Sort by use count (most used first)
        summaries.sort(key=lambda x: x['use_count'], reverse=True)
        
        return summaries
    
    def delete_template(self, name: str) -> bool:
        """
        Delete a template.
        
        Args:
            name: Template name
            
        Returns:
            True if deleted, False if not found
        """
        if name in self.templates:
            del self.templates[name]
            self._save_templates()
            self.logger.info(f"Deleted template: {name}")
            return True
        
        return False
    
    def find_matching_template(self, headers: List[str], filename: str = "") -> Optional[str]:
        """
        Find best matching template based on column headers and filename.
        
        Args:
            headers: List of column headers from catalog
            filename: Optional filename for name-based matching
            
        Returns:
            Template name if match found, None otherwise
        """
        if not self.templates:
            return None
        
        # Normalize headers for comparison
        headers_lower = [h.lower().strip() for h in headers]
        
        best_match = None
        best_score = 0.0
        
        for name, template in self.templates.items():
            score = 0.0
            
            # Check filename similarity
            if filename:
                filename_lower = filename.lower()
                name_lower = name.lower()
                if name_lower in filename_lower or filename_lower in name_lower:
                    score += 0.3
            
            # Check column header overlap
            template_columns = [c.lower() for c in template.column_mappings.keys()]
            matches = sum(1 for h in headers_lower if h in template_columns)
            
            if template_columns:
                overlap_ratio = matches / len(template_columns)
                score += overlap_ratio * 0.7
            
            if score > best_score:
                best_score = score
                best_match = name
        
        # Require minimum score for match
        if best_score >= 0.5:
            self.logger.info(f"Found matching template: {best_match} (score: {best_score:.2f})")
            return best_match
        
        return None
    
    def suggest_templates(self, headers: List[str], top_n: int = 3) -> List[Tuple[str, float]]:
        """
        Suggest possible templates based on header similarity.
        
        Args:
            headers: Column headers
            top_n: Number of suggestions to return
            
        Returns:
            List of (template_name, confidence_score) tuples
        """
        if not self.templates:
            return []
        
        headers_lower = [h.lower().strip() for h in headers]
        suggestions = []
        
        for name, template in self.templates.items():
            template_columns = [c.lower() for c in template.column_mappings.keys()]
            
            # Calculate similarity
            matches = sum(1 for h in headers_lower if h in template_columns)
            
            if template_columns:
                similarity = matches / max(len(headers_lower), len(template_columns))
                if similarity > 0.2:  # Minimum threshold
                    suggestions.append((name, similarity))
        
        # Sort by similarity (highest first)
        suggestions.sort(key=lambda x: x[1], reverse=True)
        
        return suggestions[:top_n]
    
    def export_template(self, name: str, filepath: str) -> bool:
        """
        Export template to JSON file.
        
        Args:
            name: Template name
            filepath: Output file path
            
        Returns:
            True if successful
        """
        template = self.templates.get(name)
        if not template:
            self.logger.error(f"Template not found: {name}")
            return False
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(template.to_dict(), f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Exported template to: {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting template: {str(e)}")
            return False
    
    def import_template(self, filepath: str) -> Optional[str]:
        """
        Import template from JSON file.
        
        Args:
            filepath: Path to template JSON file
            
        Returns:
            Template name if successful, None otherwise
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            template = WholesalerTemplate.from_dict(data)
            self.templates[template.name] = template
            self._save_templates()
            
            self.logger.info(f"Imported template: {template.name}")
            return template.name
            
        except Exception as e:
            self.logger.error(f"Error importing template: {str(e)}")
            return None
    
    def get_template_signature(self, headers: List[str]) -> str:
        """
        Generate a signature hash for a set of headers.
        Useful for detecting duplicate templates.
        
        Args:
            headers: Column headers
            
        Returns:
            SHA256 hash of sorted headers
        """
        sorted_headers = sorted([h.lower().strip() for h in headers])
        signature_string = '|'.join(sorted_headers)
        return hashlib.sha256(signature_string.encode()).hexdigest()[:16]
