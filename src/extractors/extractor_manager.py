"""Extractor Manager - Processes and extracts content from scraped items"""

from typing import Dict, Any, List
import logging
import hashlib
from bs4 import BeautifulSoup
from datetime import datetime


class ExtractorManager:
    """Manages content extraction and processing"""
    
    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        """
        Initialize extractor manager
        
        Args:
            config: Configuration dictionary
            logger: Logger instance
        """
        self.config = config
        self.logger = logger
    
    def extract_batch(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract content from multiple items
        
        Args:
            items: List of scraped items
            
        Returns:
            List of extracted items
        """
        self.logger.info(f"Extracting content from {len(items)} items...")
        
        extracted = []
        for item in items:
            try:
                extracted_item = self.extract(item)
                if extracted_item:
                    extracted.append(extracted_item)
            except Exception as e:
                self.logger.error(f"Extraction error: {str(e)}")
        
        self.logger.info(f"Extracted {len(extracted)} items")
        return extracted
    
    def extract(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract and normalize content from a single item
        
        Args:
            item: Scraped item dictionary
            
        Returns:
            Processed item with normalized fields
        """
        # Generate unique ID
        item['id'] = self._generate_id(item)
        
        # Normalize title
        if 'title' in item:
            item['title'] = self._normalize_title(item['title'])
        
        # Normalize authors
        if 'authors' in item:
            item['authors'] = self._normalize_authors(item['authors'])
        
        # Normalize date
        if 'published_at' in item:
            item['published_at'] = self._normalize_date(item['published_at'])
        
        # Extract text if not present
        if 'text' not in item and 'raw_text' in item:
            item['text'] = item['raw_text']
        elif 'text' not in item and 'abstract' in item:
            item['text'] = item['abstract']
        
        # Extract sections if HTML content available
        if 'html_content' in item:
            item['sections'] = self._extract_sections(item['html_content'])
        
        return item
    
    def _generate_id(self, item: Dict[str, Any]) -> str:
        """Generate unique ID for item"""
        # Prefer DOI or arXiv ID
        if 'doi' in item and item['doi']:
            return f"doi:{item['doi']}"
        
        if 'id' in item and item['id'].startswith('arXiv:'):
            return item['id']
        
        # Use canonical URL or regular URL
        url = item.get('canonical_url', item.get('url', ''))
        
        # Generate hash from URL
        return hashlib.sha256(url.encode()).hexdigest()[:16]
    
    def _normalize_title(self, title: str) -> str:
        """Normalize title"""
        # Remove extra whitespace
        title = ' '.join(title.split())
        
        # Remove trailing punctuation
        title = title.rstrip('.')
        
        return title
    
    def _normalize_authors(self, authors: List[str]) -> List[str]:
        """Normalize author names"""
        normalized = []
        
        for author in authors:
            if not author or not author.strip():
                continue
            
            # Remove extra whitespace
            author = ' '.join(author.split())
            normalized.append(author)
        
        return normalized
    
    def _normalize_date(self, date_str: str) -> str:
        """Normalize date to ISO8601 format"""
        if not date_str:
            return ""
        
        # Try various date formats
        formats = [
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%d',
            '%d %b %Y',
            '%B %d, %Y',
            '%Y/%m/%d',
            '%d/%m/%Y'
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str[:19], fmt)
                return dt.strftime('%Y-%m-%d')
            except:
                continue
        
        # If all fail, return original
        return date_str
    
    def _extract_sections(self, html: str) -> List[Dict[str, str]]:
        """Extract sections from HTML content"""
        sections = []
        
        try:
            soup = BeautifulSoup(html, 'lxml')
            
            # Find all headings and their content
            for heading in soup.find_all(['h1', 'h2', 'h3', 'h4']):
                heading_text = heading.get_text(strip=True)
                
                # Get content until next heading
                content = []
                for sibling in heading.find_next_siblings():
                    if sibling.name in ['h1', 'h2', 'h3', 'h4']:
                        break
                    if sibling.name == 'p':
                        content.append(sibling.get_text(strip=True))
                
                if content:
                    sections.append({
                        'heading': heading_text,
                        'text': '\n'.join(content)
                    })
        except Exception as e:
            self.logger.error(f"Section extraction error: {str(e)}")
        
        return sections
