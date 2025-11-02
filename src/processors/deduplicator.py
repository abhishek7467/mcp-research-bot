"""Deduplicator - Removes duplicate items"""

from typing import Dict, Any, List
import logging
from difflib import SequenceMatcher


class Deduplicator:
    """Deduplicates items based on various fingerprints"""
    
    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        """
        Initialize deduplicator
        
        Args:
            config: Configuration dictionary
            logger: Logger instance
        """
        self.config = config
        self.logger = logger
    
    def deduplicate(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicate items
        
        Args:
            items: List of items to deduplicate
            
        Returns:
            List of unique items
        """
        self.logger.info(f"Deduplicating {len(items)} items...")
        
        seen_fingerprints = {}
        unique_items = []
        duplicates = 0
        
        for item in items:
            # Generate fingerprint
            fingerprint = self._generate_fingerprint(item)
            
            # Check if seen before
            if fingerprint in seen_fingerprints:
                duplicates += 1
                
                # Keep the more complete item
                existing = seen_fingerprints[fingerprint]
                if self._is_more_complete(item, existing):
                    # Replace existing with this one
                    seen_fingerprints[fingerprint] = item
                    # Update in unique_items
                    for i, ui in enumerate(unique_items):
                        if self._generate_fingerprint(ui) == fingerprint:
                            unique_items[i] = item
                            break
                continue
            
            # New item
            seen_fingerprints[fingerprint] = item
            unique_items.append(item)
        
        self.logger.info(f"Found {duplicates} duplicates, {len(unique_items)} unique items remain")
        
        return unique_items
    
    def _generate_fingerprint(self, item: Dict[str, Any]) -> str:
        """Generate fingerprint for item"""
        # Priority: DOI > ID > normalized title+author
        
        doi = item.get('doi', '').strip()
        if doi:
            return f"doi:{doi.lower()}"
        
        item_id = item.get('id', '').strip()
        if item_id and (item_id.startswith('arXiv:') or item_id.startswith('PMID:')):
            return item_id.lower()
        
        # Generate from title + first author + year
        title = item.get('title', '').lower().strip()
        authors = item.get('authors', [])
        first_author = authors[0].lower() if authors else ''
        
        # Extract year from published_at
        published = item.get('published_at', '')
        year = published[:4] if len(published) >= 4 else ''
        
        # Normalize title (remove common words, punctuation)
        title_words = ''.join(c for c in title if c.isalnum() or c.isspace())
        title_words = ' '.join(title_words.split()[:10])  # First 10 words
        
        fingerprint = f"{title_words}|{first_author}|{year}"
        
        return fingerprint
    
    def _is_more_complete(self, item1: Dict[str, Any], item2: Dict[str, Any]) -> bool:
        """Check if item1 is more complete than item2"""
        # Count non-empty fields
        score1 = self._completeness_score(item1)
        score2 = self._completeness_score(item2)
        
        return score1 > score2
    
    def _completeness_score(self, item: Dict[str, Any]) -> int:
        """Calculate completeness score for item"""
        score = 0
        
        # Important fields
        important_fields = ['title', 'authors', 'abstract', 'text', 'pdf_url', 'doi']
        
        for field in important_fields:
            if field in item and item[field]:
                if isinstance(item[field], str):
                    score += len(item[field]) > 0
                elif isinstance(item[field], list):
                    score += len(item[field]) > 0
        
        return score
