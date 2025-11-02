"""
Summarizer Agent using Google Gemini and OpenAI

This agent generates:
- TL;DR (2-3 sentences)
- Key bullet points (5-7)
- Significance
- Limitations
- Keywords
"""

import os
from typing import Dict, Any, List, Optional
import logging
from openai import OpenAI
import google.generativeai as genai


class SummarizerAgent:
    """AI-powered summarizer using Gemini or OpenAI"""
    
    SUMMARIZER_PROMPT = """You are a concise, scientific summarizer for a daily research newspaper.

Input: Research paper or news article with the following information:
- Title: {title}
- Authors: {authors}
- Published: {published_at}
- Source: {source}
- Abstract: {abstract}
- Full Text: {full_text}

Task: Produce a structured summary in JSON format with the following fields:

1. **headline**: A compelling one-line headline (max 12 words) - factual, no clickbait
2. **tldr**: 2-3 sentences (50-70 words) summarizing what this is about and the main claim/result
3. **bullets**: Array of 5-7 bullet points, each one sentence, covering key contributions/findings
4. **significance**: 2-3 sentences explaining why this matters and its potential impact
5. **limitations**: 1-2 sentences noting caveats, limitations, or areas for future work
6. **keywords**: Array of 3-7 relevant keywords/phrases
7. **read_time_minutes**: Estimated read time for the full text (integer)

Guidelines:
- Use neutral, non-sensational tone suitable for scientific newspaper
- Use active voice and cite specific numbers/results when present
- For research papers: focus on methodology, results, and contributions
- For news articles: emphasize who/what/when/where/why/how
- Be factual and precise
- Avoid speculation

Output only valid JSON with these exact fields. No markdown, no code blocks, just the JSON object.
"""
    
    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        """
        Initialize summarizer agent
        
        Args:
            config: Configuration dictionary
            logger: Logger instance
        """
        self.config = config
        self.logger = logger
        
        # Get AI model preference
        ai_config = config.get('ai_models', {})
        self.model_choice = ai_config.get('summarizer', 'gemini')
        
        # Initialize clients
        self._init_clients(ai_config)
        
        self.logger.info(f"SummarizerAgent initialized with model: {self.model_choice}")
    
    def _init_clients(self, ai_config: Dict[str, Any]):
        """Initialize AI clients"""
        # OpenAI
        openai_key = self.config.get('api_keys', {}).get('openai', os.getenv('OPENAI_API_KEY'))
        if openai_key:
            self.openai_client = OpenAI(api_key=openai_key)
            self.openai_model = ai_config.get('openai_chat_model', 'gpt-4o')
        else:
            self.openai_client = None
            self.logger.warning("OpenAI API key not found")
        
        # Google Gemini
        gemini_key = self.config.get('api_keys', {}).get('gemini', os.getenv('GEMINI_API_KEY'))
        if gemini_key:
            genai.configure(api_key=gemini_key)
            self.gemini_model_name = ai_config.get('gemini_model', 'gemini-1.5-pro-latest')
            self.gemini_model = genai.GenerativeModel(self.gemini_model_name)
        else:
            self.gemini_model = None
            self.logger.warning("Gemini API key not found")
    
    def summarize(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate summary for a single item
        
        Args:
            item: Item dictionary with title, authors, abstract, full_text, etc.
            
        Returns:
            Item dictionary with added summary fields
        """
        try:
            # Prepare input
            title = item.get('title', '')
            authors = ', '.join(item.get('authors', []))
            published_at = item.get('published_at', 'Unknown')
            source = item.get('source', 'Unknown')
            abstract = item.get('abstract', '')
            full_text = item.get('text', '')[:4000]  # Limit text length
            
            # Format prompt
            prompt = self.SUMMARIZER_PROMPT.format(
                title=title,
                authors=authors,
                published_at=published_at,
                source=source,
                abstract=abstract,
                full_text=full_text
            )
            
            # Generate summary using selected model
            if self.model_choice == 'gemini' and self.gemini_model:
                summary = self._summarize_with_gemini(prompt)
            elif self.model_choice == 'openai' and self.openai_client:
                summary = self._summarize_with_openai(prompt)
            else:
                self.logger.error(f"No valid AI model available for summarization")
                return item
            
            # Parse and merge summary into item
            if summary:
                item.update(summary)
                self.logger.debug(f"Generated summary for: {title[:50]}...")
            
            return item
            
        except Exception as e:
            self.logger.error(f"Error summarizing item: {str(e)}", exc_info=True)
            return item
    
    def _summarize_with_gemini(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Generate summary using Google Gemini"""
        try:
            # Configure generation
            generation_config = {
                'temperature': 0.3,
                'top_p': 0.95,
                'top_k': 40,
                'max_output_tokens': 2048,
            }
            
            response = self.gemini_model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            # Extract JSON from response
            import json
            text = response.text.strip()
            
            # Remove markdown code blocks if present
            if text.startswith('```json'):
                text = text[7:]
            if text.startswith('```'):
                text = text[3:]
            if text.endswith('```'):
                text = text[:-3]
            
            summary = json.loads(text.strip())
            return summary
            
        except Exception as e:
            self.logger.error(f"Gemini summarization failed: {str(e)}")
            return None
    
    def _summarize_with_openai(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Generate summary using OpenAI"""
        try:
            response = self.openai_client.chat.completions.create(
                model=self.openai_model,
                messages=[
                    {"role": "system", "content": "You are a scientific summarizer. Output only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            import json
            summary = json.loads(response.choices[0].message.content)
            return summary
            
        except Exception as e:
            self.logger.error(f"OpenAI summarization failed: {str(e)}")
            return None
    
    def summarize_batch(self, items: List[Dict[str, Any]], max_workers: int = 5) -> List[Dict[str, Any]]:
        """
        Summarize multiple items in parallel
        
        Args:
            items: List of items to summarize
            max_workers: Maximum parallel workers
            
        Returns:
            List of items with summaries
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed
        from tqdm import tqdm
        
        self.logger.info(f"Summarizing {len(items)} items with {max_workers} workers...")
        
        summarized = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_item = {
                executor.submit(self.summarize, item): item 
                for item in items
            }
            
            # Process completed tasks with progress bar
            with tqdm(total=len(items), desc="Summarizing") as pbar:
                for future in as_completed(future_to_item):
                    try:
                        result = future.result()
                        summarized.append(result)
                    except Exception as e:
                        self.logger.error(f"Batch summarization error: {str(e)}")
                        summarized.append(future_to_item[future])  # Add original item
                    finally:
                        pbar.update(1)
        
        self.logger.info(f"Completed summarization: {len(summarized)} items")
        return summarized
