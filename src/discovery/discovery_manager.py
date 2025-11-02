"""
Discovery Manager - Discovers research papers and news from multiple sources

Uses APIs and RSS feeds to find new content:
- arXiv API
- Crossref API
- PubMed API
- bioRxiv API
- RSS feeds from journals and news sites
"""

import requests
import feedparser
from typing import List, Dict, Any
from datetime import datetime, timedelta
import logging
from urllib.parse import quote


class DiscoveryManager:
    """Manages discovery from multiple sources"""
    
    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        """
        Initialize discovery manager
        
        Args:
            config: Configuration dictionary
            logger: Logger instance
        """
        self.config = config
        self.logger = logger
        self.session = requests.Session()
        
        # Set user agent
        user_agent = config.get('crawling', {}).get('user_agent', 'MCP-Research-Bot/1.0')
        self.session.headers.update({'User-Agent': user_agent})
        
    def discover_all(self, topics: List[str], date: str = None) -> List[Dict[str, Any]]:
        """
        Discover content from all sources
        
        Args:
            topics: List of topics to search
            date: Date to search for (YYYY-MM-DD)
            
        Returns:
            List of discovered items
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        # Calculate date window
        backfill_days = self.config.get('schedule', {}).get('backfill_days', 2)
        start_date = (datetime.strptime(date, '%Y-%m-%d') - timedelta(days=backfill_days)).strftime('%Y-%m-%d')
        
        self.logger.info(f"Discovering content from {start_date} to {date}")
        
        all_items = []
        
        # Discover from research APIs
        research_sources = self.config.get('research_sources', {}).get('apis', [])
        for source in research_sources:
            if not source.get('enabled', True):
                continue
            
            try:
                items = self._discover_from_api(source, topics, start_date, date)
                all_items.extend(items)
                self.logger.info(f"Discovered {len(items)} items from {source['name']}")
            except Exception as e:
                self.logger.error(f"Error discovering from {source['name']}: {str(e)}")
        
        # Discover from RSS feeds
        journal_feeds = self.config.get('research_sources', {}).get('journals', [])
        for journal in journal_feeds:
            try:
                items = self._discover_from_rss(journal)
                all_items.extend(items)
                self.logger.info(f"Discovered {len(items)} items from {journal['name']}")
            except Exception as e:
                self.logger.error(f"Error discovering from {journal['name']}: {str(e)}")
        
        # Discover news
        news_sources = self.config.get('news_sources', [])
        for source in news_sources:
            try:
                items = self._discover_news(source, topics)
                all_items.extend(items)
                self.logger.info(f"Discovered {len(items)} news items from {source['name']}")
            except Exception as e:
                self.logger.error(f"Error discovering from {source['name']}: {str(e)}")
        
        self.logger.info(f"Total discovered: {len(all_items)} items")
        return all_items
    
    def _discover_from_api(self, source: Dict, topics: List[str], start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Discover from research APIs"""
        
        if source['name'] == 'arXiv':
            return self._discover_arxiv(topics, start_date, end_date)
        elif source['name'] == 'Crossref':
            return self._discover_crossref(topics, start_date, end_date)
        elif source['name'] == 'PubMed':
            return self._discover_pubmed(topics, start_date, end_date)
        elif source['name'] == 'bioRxiv':
            return self._discover_biorxiv(topics, start_date, end_date)
        else:
            return []
    
    def _discover_arxiv(self, topics: List[str], start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Discover from arXiv API"""
        items = []
        base_url = "http://export.arxiv.org/api/query"
        
        max_results = self.config.get('crawling', {}).get('max_crawl_per_source', 200)
        
        for topic in topics:
            # Build query
            query = f'search_query=all:{quote(topic)}&start=0&max_results={max_results}&sortBy=submittedDate&sortOrder=descending'
            url = f"{base_url}?{query}"
            
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                
                # Parse Atom feed
                feed = feedparser.parse(response.content)
                
                for entry in feed.entries:
                    # Extract data
                    item = {
                        'id': entry.id.split('/abs/')[-1],
                        'url': entry.link,
                        'title': entry.title,
                        'authors': [author.name for author in entry.authors],
                        'abstract': entry.summary,
                        'published_at': entry.published,
                        'source': 'arXiv',
                        'type': 'research',
                        'pdf_url': entry.link.replace('/abs/', '/pdf/') + '.pdf',
                        'categories': [tag.term for tag in entry.tags] if hasattr(entry, 'tags') else []
                    }
                    items.append(item)
                    
            except Exception as e:
                self.logger.error(f"arXiv API error for topic '{topic}': {str(e)}")
        
        return items
    
    def _discover_crossref(self, topics: List[str], start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Discover from Crossref API"""
        items = []
        base_url = "https://api.crossref.org/works"
        
        email = self.config.get('api_keys', {}).get('crossref_email', '')
        max_results = self.config.get('crawling', {}).get('max_crawl_per_source', 200)
        
        for topic in topics:
            try:
                params = {
                    'query': topic,
                    'filter': f'from-pub-date:{start_date},until-pub-date:{end_date}',
                    'rows': min(max_results, 100),
                    'sort': 'published',
                    'order': 'desc',
                    'mailto': email
                }
                
                response = self.session.get(base_url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                for work in data.get('message', {}).get('items', []):
                    # Extract data
                    item = {
                        'id': work.get('DOI', ''),
                        'url': work.get('URL', f"https://doi.org/{work.get('DOI', '')}"),
                        'title': work.get('title', [''])[0],
                        'authors': [f"{a.get('given', '')} {a.get('family', '')}" for a in work.get('author', [])],
                        'abstract': work.get('abstract', ''),
                        'published_at': self._parse_crossref_date(work.get('published', {})),
                        'source': 'Crossref',
                        'type': 'research',
                        'doi': work.get('DOI', ''),
                        'journal': work.get('container-title', [''])[0],
                        'publisher': work.get('publisher', '')
                    }
                    items.append(item)
                    
            except Exception as e:
                self.logger.error(f"Crossref API error for topic '{topic}': {str(e)}")
        
        return items
    
    def _discover_pubmed(self, topics: List[str], start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Discover from PubMed API"""
        items = []
        base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
        max_results = self.config.get('crawling', {}).get('max_crawl_per_source', 200)
        
        for topic in topics:
            try:
                # Search for IDs
                search_url = f"{base_url}esearch.fcgi"
                search_params = {
                    'db': 'pubmed',
                    'term': topic,
                    'retmax': max_results,
                    'retmode': 'json',
                    'datetype': 'pdat',
                    'mindate': start_date.replace('-', '/'),
                    'maxdate': end_date.replace('-', '/'),
                    'sort': 'date'
                }
                
                response = self.session.get(search_url, params=search_params, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                ids = data.get('esearchresult', {}).get('idlist', [])
                
                if not ids:
                    continue
                
                # Fetch summaries
                summary_url = f"{base_url}esummary.fcgi"
                summary_params = {
                    'db': 'pubmed',
                    'id': ','.join(ids[:50]),  # Limit batch size
                    'retmode': 'json'
                }
                
                response = self.session.get(summary_url, params=summary_params, timeout=30)
                response.raise_for_status()
                summaries = response.json()
                
                for pmid, summary in summaries.get('result', {}).items():
                    if pmid == 'uids':
                        continue
                    
                    item = {
                        'id': f"PMID:{pmid}",
                        'url': f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                        'title': summary.get('title', ''),
                        'authors': [a.get('name', '') for a in summary.get('authors', [])],
                        'abstract': '',  # Requires separate fetch
                        'published_at': summary.get('pubdate', ''),
                        'source': 'PubMed',
                        'type': 'research',
                        'journal': summary.get('source', ''),
                        'doi': summary.get('elocationid', '') if 'doi' in summary.get('elocationid', '').lower() else ''
                    }
                    items.append(item)
                    
            except Exception as e:
                self.logger.error(f"PubMed API error for topic '{topic}': {str(e)}")
        
        return items
    
    def _discover_biorxiv(self, topics: List[str], start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Discover from bioRxiv API"""
        items = []
        base_url = "https://api.biorxiv.org/details/biorxiv"
        
        try:
            # bioRxiv API uses dates in YYYY-MM-DD format
            url = f"{base_url}/{start_date}/{end_date}"
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            for paper in data.get('collection', []):
                # Check if relevant to topics
                title_abstract = f"{paper.get('title', '')} {paper.get('abstract', '')}".lower()
                if not any(topic.lower() in title_abstract for topic in topics):
                    continue
                
                item = {
                    'id': paper.get('doi', ''),
                    'url': f"https://www.biorxiv.org/content/{paper.get('doi', '')}v{paper.get('version', '1')}",
                    'title': paper.get('title', ''),
                    'authors': paper.get('authors', '').split(';'),
                    'abstract': paper.get('abstract', ''),
                    'published_at': paper.get('date', ''),
                    'source': 'bioRxiv',
                    'type': 'research',
                    'doi': paper.get('doi', ''),
                    'category': paper.get('category', '')
                }
                items.append(item)
                
        except Exception as e:
            self.logger.error(f"bioRxiv API error: {str(e)}")
        
        return items
    
    def _discover_from_rss(self, journal: Dict) -> List[Dict[str, Any]]:
        """Discover from RSS feeds"""
        items = []
        
        try:
            feed = feedparser.parse(journal.get('rss', ''))
            
            for entry in feed.entries[:50]:  # Limit entries
                item = {
                    'id': entry.get('id', entry.get('link', '')),
                    'url': entry.get('link', ''),
                    'title': entry.get('title', ''),
                    'authors': [entry.get('author', '')] if entry.get('author') else [],
                    'abstract': entry.get('summary', ''),
                    'published_at': entry.get('published', entry.get('updated', '')),
                    'source': journal.get('name', ''),
                    'type': 'research'
                }
                items.append(item)
                
        except Exception as e:
            self.logger.error(f"RSS feed error for {journal.get('name', 'Unknown')}: {str(e)}")
        
        return items
    
    def _discover_news(self, source: Dict, topics: List[str]) -> List[Dict[str, Any]]:
        """Discover news from RSS or search"""
        items = []
        
        # Check if RSS feed exists
        if 'rss' in source:
            feed_url = source['rss']
        elif 'search_url' in source:
            # Google News style search
            topic_query = ' OR '.join(topics)
            feed_url = source['search_url'].format(topic=quote(topic_query))
        else:
            return items
        
        try:
            feed = feedparser.parse(feed_url)
            
            for entry in feed.entries[:20]:  # Limit news entries
                item = {
                    'id': entry.get('id', entry.get('link', '')),
                    'url': entry.get('link', ''),
                    'title': entry.get('title', ''),
                    'authors': [entry.get('author', '')] if entry.get('author') else [],
                    'abstract': entry.get('summary', ''),
                    'published_at': entry.get('published', entry.get('updated', '')),
                    'source': source.get('name', ''),
                    'type': 'news'
                }
                items.append(item)
                
        except Exception as e:
            self.logger.error(f"News discovery error for {source.get('name', 'Unknown')}: {str(e)}")
        
        return items
    
    def _parse_crossref_date(self, date_parts: Dict) -> str:
        """Parse Crossref date format"""
        try:
            parts = date_parts.get('date-parts', [[]])[0]
            if len(parts) >= 3:
                return f"{parts[0]:04d}-{parts[1]:02d}-{parts[2]:02d}"
            elif len(parts) == 2:
                return f"{parts[0]:04d}-{parts[1]:02d}-01"
            elif len(parts) == 1:
                return f"{parts[0]:04d}-01-01"
        except:
            pass
        return ""
