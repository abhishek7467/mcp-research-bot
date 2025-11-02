"""
Relevance Scorer - Scores and ranks items by relevance, recency, credibility, and novelty

Uses OpenAI embeddings for semantic similarity (Gemini embeddings coming soon)
"""

import os
from typing import Dict, Any, List
import logging
from datetime import datetime
import numpy as np
from openai import OpenAI


class RelevanceScorer:
    """Scores and ranks items"""
    
    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        """
        Initialize relevance scorer
        
        Args:
            config: Configuration dictionary
            logger: Logger instance
        """
        self.config = config
        self.logger = logger
        
        # Initialize OpenAI for embeddings (optional if using Gemini only)
        openai_key = config.get('api_keys', {}).get('openai', os.getenv('OPENAI_API_KEY'))
        if openai_key:
            self.openai_client = OpenAI(api_key=openai_key)
            self.embedding_model = config.get('ai_models', {}).get('openai_embedding_model', 'text-embedding-3-small')
        else:
            self.openai_client = None
            self.logger.warning("OpenAI API key not found - will use fallback keyword matching")
        
        # Scoring weights
        weights = config.get('scoring', {}).get('weights', {})
        self.weight_relevance = weights.get('relevance', 0.35)
        self.weight_recency = weights.get('recency', 0.25)
        self.weight_credibility = weights.get('credibility', 0.20)
        self.weight_novelty = weights.get('novelty', 0.20)
        
        # Publisher credibility scores
        self.credibility_scores = {
            'arxiv': 0.85,
            'pubmed': 0.90,
            'nature': 0.95,
            'science': 0.95,
            'cell': 0.90,
            'lancet': 0.90,
            'mit technology review': 0.85,
            'ars technica': 0.75,
            'the verge': 0.70,
            'default': 0.60
        }
    
    def score_and_rank(self, items: List[Dict[str, Any]], topics: List[str]) -> List[Dict[str, Any]]:
        """
        Score and rank items
        
        Args:
            items: List of items to score
            topics: List of topics for relevance scoring
            
        Returns:
            List of items sorted by score (descending)
        """
        self.logger.info(f"Scoring {len(items)} items...")
        
        # Get topic embeddings if OpenAI available
        topic_embeddings = []
        if self.openai_client:
            for topic in topics:
                emb = self._get_embedding(topic)
                if emb is not None:
                    topic_embeddings.append(emb)
        
        # Score each item
        for item in items:
            scores = {
                'relevance': self._score_relevance(item, topics, topic_embeddings),
                'recency': self._score_recency(item),
                'credibility': self._score_credibility(item),
                'novelty': self._score_novelty(item)
            }
            
            # Calculate weighted total
            total_score = (
                scores['relevance'] * self.weight_relevance +
                scores['recency'] * self.weight_recency +
                scores['credibility'] * self.weight_credibility +
                scores['novelty'] * self.weight_novelty
            )
            
            item['score'] = total_score
            item['score_breakdown'] = scores
        
        # Sort by score
        items.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        if items:
            self.logger.info(f"Scoring complete. Top score: {items[0].get('score', 0):.3f}")
        
        return items
    
    def _score_relevance(self, item: Dict[str, Any], topics: List[str], topic_embeddings: List) -> float:
        """Score relevance using embeddings or keyword matching"""
        if not self.openai_client or not topic_embeddings:
            # Fallback: keyword matching
            text = f"{item.get('title', '')} {item.get('abstract', '')}".lower()
            matches = sum(1 for topic in topics if topic.lower() in text)
            return min(matches / len(topics), 1.0)
        
        # Get item embedding
        item_text = f"{item.get('title', '')} {item.get('abstract', '')}"
        item_embedding = self._get_embedding(item_text)
        
        if item_embedding is None:
            return 0.5  # Default
        
        # Calculate max similarity with topics
        max_similarity = 0.0
        for topic_emb in topic_embeddings:
            similarity = self._cosine_similarity(item_embedding, topic_emb)
            max_similarity = max(max_similarity, similarity)
        
        return max_similarity
    
    def _score_recency(self, item: Dict[str, Any]) -> float:
        """Score based on recency (newer = higher)"""
        published_str = item.get('published_at', '')
        
        if not published_str:
            return 0.5  # Default
        
        try:
            # Parse date
            if 'T' in published_str:
                published = datetime.fromisoformat(published_str.replace('Z', '+00:00'))
            else:
                published = datetime.strptime(published_str[:10], '%Y-%m-%d')
            
            # Calculate days ago
            days_ago = (datetime.now() - published).days
            
            # Score decays over 30 days
            if days_ago < 0:
                return 1.0
            elif days_ago > 30:
                return 0.3
            else:
                return 1.0 - (days_ago / 30.0) * 0.7
                
        except Exception as e:
            self.logger.debug(f"Date parsing error: {str(e)}")
            return 0.5
    
    def _score_credibility(self, item: Dict[str, Any]) -> float:
        """Score based on source credibility"""
        source = item.get('source', '').lower()
        journal = item.get('journal', '').lower()
        
        # Check source first
        for key, score in self.credibility_scores.items():
            if key in source:
                return score
        
        # Check journal
        for key, score in self.credibility_scores.items():
            if key in journal:
                return score
        
        # Check if has DOI (more credible)
        if item.get('doi'):
            return 0.75
        
        return self.credibility_scores['default']
    
    def _score_novelty(self, item: Dict[str, Any]) -> float:
        """Score novelty"""
        source = item.get('source', '').lower()
        
        if 'arxiv' in source or 'biorxiv' in source or 'medrxiv' in source:
            return 0.9  # Preprints are novel
        elif item.get('doi'):
            return 0.7  # Published papers
        else:
            return 0.6  # News
    
    def _get_embedding(self, text: str) -> List[float]:
        """Get embedding for text using OpenAI"""
        if not self.openai_client:
            return None
        
        try:
            # Limit text length
            text = text[:8000]
            
            response = self.openai_client.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            
            return response.data[0].embedding
            
        except Exception as e:
            self.logger.error(f"Embedding error: {str(e)}")
            return None
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
