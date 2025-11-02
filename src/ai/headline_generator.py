"""
Headline Generator using Google Gemini and OpenAI

Generates compelling but factual headlines for newspaper sections
"""

import os
from typing import Dict, Any, List, Optional
import logging
from openai import OpenAI
import google.generativeai as genai


class HeadlineGenerator:
    """AI-powered headline generator"""
    
    HEADLINE_PROMPT = """You are a headline writer for a scientific newspaper.

Given this article information:
- Title: {title}
- TL;DR: {tldr}
- Source: {source}
- Type: {item_type}

Generate a compelling but factual headline that:
1. Is 8-12 words maximum
2. Captures the key finding or news
3. Is specific and informative (not clickbait)
4. Uses active voice when possible
5. Includes numbers/results when relevant
6. Is appropriate for a {item_type} article

Output only the headline text, nothing else. No quotes, no punctuation at the end unless it's a question.
"""
    
    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        """
        Initialize headline generator
        
        Args:
            config: Configuration dictionary
            logger: Logger instance
        """
        self.config = config
        self.logger = logger
        
        # Get AI model preference
        ai_config = config.get('ai_models', {})
        self.model_choice = ai_config.get('headline_generator', 'gemini')
        
        # Initialize clients
        self._init_clients(ai_config)
        
        self.logger.info(f"HeadlineGenerator initialized with model: {self.model_choice}")
    
    def _init_clients(self, ai_config: Dict[str, Any]):
        """Initialize AI clients"""
        # OpenAI
        openai_key = self.config.get('api_keys', {}).get('openai', os.getenv('OPENAI_API_KEY'))
        if openai_key:
            self.openai_client = OpenAI(api_key=openai_key)
            self.openai_model = ai_config.get('openai_chat_model', 'gpt-4o')
        else:
            self.openai_client = None
        
        # Google Gemini
        gemini_key = self.config.get('api_keys', {}).get('gemini', os.getenv('GEMINI_API_KEY'))
        if gemini_key:
            genai.configure(api_key=gemini_key)
            self.gemini_model_name = ai_config.get('gemini_model', 'gemini-1.5-flash')  # Use flash for headlines
            self.gemini_model = genai.GenerativeModel(self.gemini_model_name)
        else:
            self.gemini_model = None
    
    def generate_headline(self, item: Dict[str, Any]) -> str:
        """
        Generate headline for a single item
        
        Args:
            item: Item dictionary
            
        Returns:
            Generated headline string
        """
        try:
            # Use existing headline if good quality
            if 'headline' in item and item['headline']:
                return item['headline']
            
            # Prepare input
            title = item.get('title', '')
            tldr = item.get('tldr', '')
            source = item.get('source', 'Unknown')
            item_type = item.get('type', 'research')  # research or news
            
            # Format prompt
            prompt = self.HEADLINE_PROMPT.format(
                title=title,
                tldr=tldr,
                source=source,
                item_type=item_type
            )
            
            # Generate headline
            if self.model_choice == 'gemini' and self.gemini_model:
                headline = self._generate_with_gemini(prompt)
            elif self.model_choice == 'openai' and self.openai_client:
                headline = self._generate_with_openai(prompt)
            else:
                # Fallback: use title
                headline = title[:80]
            
            return headline.strip()
            
        except Exception as e:
            self.logger.error(f"Error generating headline: {str(e)}")
            return item.get('title', 'Untitled')[:80]
    
    def _generate_with_gemini(self, prompt: str) -> str:
        """Generate headline using Google Gemini"""
        try:
            generation_config = {
                'temperature': 0.7,
                'top_p': 0.9,
                'max_output_tokens': 50,
            }
            
            response = self.gemini_model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            return response.text.strip()
            
        except Exception as e:
            self.logger.error(f"Gemini headline generation failed: {str(e)}")
            return ""
    
    def _generate_with_openai(self, prompt: str) -> str:
        """Generate headline using OpenAI"""
        try:
            response = self.openai_client.chat.completions.create(
                model=self.openai_model,
                messages=[
                    {"role": "system", "content": "You are a headline writer. Output only the headline."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=50
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            self.logger.error(f"OpenAI headline generation failed: {str(e)}")
            return ""
    
    def generate_headlines(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate headlines for multiple items
        
        Args:
            items: List of items
            
        Returns:
            List of items with generated headlines
        """
        from tqdm import tqdm
        
        self.logger.info(f"Generating headlines for {len(items)} items...")
        
        for item in tqdm(items, desc="Headlines"):
            if 'headline' not in item or not item['headline']:
                item['headline'] = self.generate_headline(item)
        
        return items
    
    def assign_sections(self, items: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Assign items to newspaper sections
        
        Sections:
        - top_research: Highest-scoring research papers
        - rapid_news: Breaking news & press releases
        - methods_tools: Software, datasets, tools
        - short_briefs: Very short items
        - full_summaries: Expanded writeups
        
        Args:
            items: List of scored items
            
        Returns:
            Dictionary mapping section names to items
        """
        sections = {
            'top_research': [],
            'rapid_news': [],
            'methods_tools': [],
            'short_briefs': [],
            'full_summaries': []
        }
        
        # Sort by score
        sorted_items = sorted(items, key=lambda x: x.get('score', 0), reverse=True)
        
        max_top = self.config.get('processing', {}).get('top_research_picks', 5)
        max_news = self.config.get('processing', {}).get('rapid_news_count', 7)
        
        for item in sorted_items:
            item_type = item.get('type', 'research')
            title_lower = item.get('title', '').lower()
            
            # Assign to sections based on type and content
            if item_type == 'research' and len(sections['top_research']) < max_top:
                sections['top_research'].append(item)
            elif item_type == 'news' and len(sections['rapid_news']) < max_news:
                sections['rapid_news'].append(item)
            elif any(kw in title_lower for kw in ['tool', 'software', 'dataset', 'library', 'framework']):
                sections['methods_tools'].append(item)
            elif len(item.get('abstract', '')) < 200:
                sections['short_briefs'].append(item)
            else:
                sections['full_summaries'].append(item)
        
        self.logger.info(f"Section assignment: {', '.join([f'{k}={len(v)}' for k, v in sections.items()])}")
        
        return sections
