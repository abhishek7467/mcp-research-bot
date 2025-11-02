"""
Index Manager - Manages search indexes for efficient retrieval

Creates and maintains indexes for fast lookup of articles by topic, date, etc.
"""

import os
import json
from typing import Dict, Any, List
import logging
from datetime import datetime


class IndexManager:
    """Manages search indexes"""
    
    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        """
        Initialize index manager
        
        Args:
            config: Configuration dictionary
            logger: Logger instance
        """
        self.config = config
        self.logger = logger
        
        # Index directory
        self.index_dir = config.get('storage', {}).get('index_dir', 'data/indexes')
        os.makedirs(self.index_dir, exist_ok=True)
        
        # Load indexes
        self.topic_index = self._load_index('topics.json')
        self.date_index = self._load_index('dates.json')
        self.source_index = self._load_index('sources.json')
    
    def add_items(self, items: List[Dict[str, Any]]) -> None:
        """
        Add items to indexes
        
        Args:
            items: List of items to index
        """
        self.logger.info(f"Indexing {len(items)} items...")
        
        for item in items:
            item_id = item.get('id', item.get('title', ''))
            
            # Index by topics
            topics = item.get('topics', [])
            for topic in topics:
                if topic not in self.topic_index:
                    self.topic_index[topic] = []
                if item_id not in self.topic_index[topic]:
                    self.topic_index[topic].append(item_id)
            
            # Index by date
            published_at = item.get('published_at', '')
            if published_at:
                date_key = published_at[:10]  # YYYY-MM-DD
                if date_key not in self.date_index:
                    self.date_index[date_key] = []
                if item_id not in self.date_index[date_key]:
                    self.date_index[date_key].append(item_id)
            
            # Index by source
            source = item.get('source', 'unknown')
            if source not in self.source_index:
                self.source_index[source] = []
            if item_id not in self.source_index[source]:
                self.source_index[source].append(item_id)
        
        # Save indexes
        self._save_index('topics.json', self.topic_index)
        self._save_index('dates.json', self.date_index)
        self._save_index('sources.json', self.source_index)
        
        self.logger.info("Indexing complete")
    
    def search_by_topic(self, topic: str) -> List[str]:
        """Get item IDs for a topic"""
        return self.topic_index.get(topic, [])
    
    def search_by_date(self, date: str) -> List[str]:
        """Get item IDs for a date (YYYY-MM-DD)"""
        return self.date_index.get(date, [])
    
    def search_by_source(self, source: str) -> List[str]:
        """Get item IDs for a source"""
        return self.source_index.get(source, [])
    
    def _load_index(self, filename: str) -> Dict[str, List[str]]:
        """Load an index from disk"""
        filepath = os.path.join(self.index_dir, filename)
        
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Error loading index {filename}: {str(e)}")
        
        return {}
    
    def _save_index(self, filename: str, index: Dict[str, List[str]]) -> None:
        """Save an index to disk"""
        filepath = os.path.join(self.index_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(index, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Error saving index {filename}: {str(e)}")
