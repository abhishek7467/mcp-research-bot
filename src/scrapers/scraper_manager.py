"""
Scraper Manager - Fetches and parses content from URLs

Respects robots.txt, rate limits, and extracts metadata
"""

import requests
import time
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser
from bs4 import BeautifulSoup
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm


class ScraperManager:
    """Manages scraping with robots.txt compliance and rate limiting"""
    
    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        """
        Initialize scraper manager
        
        Args:
            config: Configuration dictionary
            logger: Logger instance
        """
        self.config = config
        self.logger = logger
        
        # Setup session
        self.session = requests.Session()
        user_agent = config.get('crawling', {}).get('user_agent', 'MCP-Research-Bot/1.0')
        self.session.headers.update({'User-Agent': user_agent})
        
        # Rate limiting
        self.rate_limit = config.get('crawling', {}).get('rate_limit_per_second', 1.0)
        self.last_request_time = {}
        
        # Robots.txt cache
        self.robots_cache = {}
        self.respect_robots = config.get('crawling', {}).get('respect_robots_txt', True)
        
    def scrape_batch(self, items: List[Dict[str, Any]], max_workers: int = 5) -> List[Dict[str, Any]]:
        """
        Scrape multiple items in parallel
        
        Args:
            items: List of items with URLs to scrape
            max_workers: Maximum concurrent workers
            
        Returns:
            List of scraped items
        """
        self.logger.info(f"Scraping {len(items)} items with {max_workers} workers...")
        
        scraped = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_item = {
                executor.submit(self.scrape, item): item 
                for item in items
            }
            
            with tqdm(total=len(items), desc="Scraping") as pbar:
                for future in as_completed(future_to_item):
                    try:
                        result = future.result()
                        if result:
                            scraped.append(result)
                    except Exception as e:
                        self.logger.error(f"Scraping error: {str(e)}")
                    finally:
                        pbar.update(1)
        
        self.logger.info(f"Successfully scraped {len(scraped)}/{len(items)} items")
        return scraped
    
    def scrape(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Scrape a single item
        
        Args:
            item: Item dictionary with URL
            
        Returns:
            Scraped item with additional metadata
        """
        url = item.get('url', '')
        
        if not url:
            self.logger.warning("No URL provided for item")
            return None
        
        try:
            # Check robots.txt
            if self.respect_robots and not self._can_fetch(url):
                self.logger.info(f"Robots.txt disallows: {url}")
                item['fetch_status'] = 'robots_disallowed'
                return item
            
            # Rate limiting
            self._wait_for_rate_limit(url)
            
            # Fetch page
            timeout = self.config.get('crawling', {}).get('timeout_seconds', 30)
            response = self.session.get(url, timeout=timeout, allow_redirects=True)
            response.raise_for_status()
            
            # Parse content
            soup = BeautifulSoup(response.content, 'lxml')
            
            # Extract metadata
            metadata = self._extract_metadata(soup, url)
            
            # Merge with existing item
            for key, value in metadata.items():
                if not item.get(key):  # Don't overwrite existing data
                    item[key] = value
            
            # Add fetch metadata
            item['fetch_status'] = 'success'
            item['fetch_meta'] = {
                'http_status': response.status_code,
                'content_type': response.headers.get('Content-Type', ''),
                'length_bytes': len(response.content),
                'final_url': response.url
            }
            
            # Extract body text
            item['html_content'] = str(soup)[:10000]  # Limit HTML size
            item['raw_text'] = self._extract_text(soup)
            
            return item
            
        except requests.exceptions.Timeout:
            self.logger.warning(f"Timeout scraping: {url}")
            item['fetch_status'] = 'timeout'
            return item
        except requests.exceptions.RequestException as e:
            self.logger.warning(f"Request error scraping {url}: {str(e)}")
            item['fetch_status'] = 'error'
            item['error'] = str(e)
            return item
        except Exception as e:
            self.logger.error(f"Unexpected error scraping {url}: {str(e)}")
            item['fetch_status'] = 'error'
            item['error'] = str(e)
            return item
    
    def _can_fetch(self, url: str) -> bool:
        """Check if URL can be fetched according to robots.txt"""
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        
        if base_url not in self.robots_cache:
            rp = RobotFileParser()
            robots_url = urljoin(base_url, '/robots.txt')
            
            try:
                rp.set_url(robots_url)
                rp.read()
                self.robots_cache[base_url] = rp
            except:
                # If robots.txt can't be read, allow fetching
                self.robots_cache[base_url] = None
        
        rp = self.robots_cache[base_url]
        if rp is None:
            return True
        
        user_agent = self.config.get('crawling', {}).get('user_agent', '*')
        return rp.can_fetch(user_agent, url)
    
    def _wait_for_rate_limit(self, url: str):
        """Enforce rate limiting per domain"""
        parsed = urlparse(url)
        domain = parsed.netloc
        
        if domain in self.last_request_time:
            elapsed = time.time() - self.last_request_time[domain]
            wait_time = (1.0 / self.rate_limit) - elapsed
            
            if wait_time > 0:
                time.sleep(wait_time)
        
        self.last_request_time[domain] = time.time()
    
    def _extract_metadata(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract metadata from HTML"""
        metadata = {}
        
        # Title
        title_tag = soup.find('meta', {'name': 'citation_title'}) or \
                    soup.find('meta', {'property': 'og:title'}) or \
                    soup.find('title')
        if title_tag:
            metadata['title'] = title_tag.get('content', title_tag.get_text()).strip()
        
        # Authors
        author_tags = soup.find_all('meta', {'name': 'citation_author'}) or \
                     soup.find_all('meta', {'name': 'author'})
        if author_tags:
            metadata['authors'] = [tag.get('content', '').strip() for tag in author_tags]
        
        # Abstract/Description
        abstract_tag = soup.find('meta', {'name': 'citation_abstract'}) or \
                      soup.find('meta', {'name': 'description'}) or \
                      soup.find('meta', {'property': 'og:description'})
        if abstract_tag:
            metadata['abstract'] = abstract_tag.get('content', '').strip()
        
        # Publication date
        date_tag = soup.find('meta', {'name': 'citation_publication_date'}) or \
                  soup.find('meta', {'property': 'article:published_time'})
        if date_tag:
            metadata['published_at'] = date_tag.get('content', '').strip()
        
        # Journal/Publisher
        journal_tag = soup.find('meta', {'name': 'citation_journal_title'}) or \
                     soup.find('meta', {'name': 'citation_publisher'})
        if journal_tag:
            metadata['journal'] = journal_tag.get('content', '').strip()
        
        # DOI
        doi_tag = soup.find('meta', {'name': 'citation_doi'})
        if doi_tag:
            metadata['doi'] = doi_tag.get('content', '').strip()
        
        # PDF URL
        pdf_tag = soup.find('meta', {'name': 'citation_pdf_url'}) or \
                 soup.find('link', {'rel': 'alternate', 'type': 'application/pdf'})
        if pdf_tag:
            pdf_url = pdf_tag.get('content', pdf_tag.get('href', ''))
            if pdf_url:
                metadata['pdf_url'] = urljoin(url, pdf_url)
        
        # Canonical URL
        canonical_tag = soup.find('link', {'rel': 'canonical'})
        if canonical_tag:
            metadata['canonical_url'] = canonical_tag.get('href', '')
        
        return metadata
    
    def _extract_text(self, soup: BeautifulSoup) -> str:
        """Extract main text content from HTML"""
        # Remove script and style elements
        for script in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            script.decompose()
        
        # Try to find article body
        article = soup.find('article') or \
                 soup.find('div', class_=lambda x: x and 'article' in x.lower()) or \
                 soup.find('div', class_=lambda x: x and 'content' in x.lower()) or \
                 soup.find('main')
        
        if article:
            text = article.get_text(separator='\n', strip=True)
        else:
            text = soup.get_text(separator='\n', strip=True)
        
        # Clean up text
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        text = '\n'.join(lines)
        
        return text[:10000]  # Limit text length
