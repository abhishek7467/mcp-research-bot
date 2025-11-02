"""
MCP Server - Main Orchestrator
Daily Research + News Newspaper Generator

This is the main entry point that coordinates the entire pipeline:
1. Discovery (APIs + RSS + search)
2. Fetch metadata & HTML
3. Extract & canonicalize
4. Dedupe & compute embeddings
5. Score & rank
6. Summarize
7. Generate newspaper
"""

import os
import sys
import logging
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any
import yaml
from dotenv import load_dotenv

# Import our modules
from src.utils.logger import setup_logger
from src.utils.config_loader import ConfigLoader
from src.discovery.discovery_manager import DiscoveryManager
from src.scrapers.scraper_manager import ScraperManager
from src.extractors.extractor_manager import ExtractorManager
from src.processors.deduplicator import Deduplicator
from src.processors.scorer import RelevanceScorer
from src.ai.summarizer import SummarizerAgent
from src.ai.headline_generator import HeadlineGenerator
from src.generators.newspaper_generator import NewspaperGenerator
from src.storage.database import DatabaseManager
from src.storage.index_manager import IndexManager
from src.utils.notifier import Notifier


class MCPOrchestrator:
    """Main orchestrator for the MCP Research + News Pipeline"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """Initialize the orchestrator"""
        # Load environment variables
        load_dotenv()
        
        # Load configuration
        self.config = ConfigLoader(config_path).load()
        
        # Setup logging
        self.logger = setup_logger(
            level=self.config.get('logging', {}).get('level', 'INFO'),
            log_file=self.config.get('logging', {}).get('file', 'logs/mcp.log')
        )
        
        self.logger.info("=" * 80)
        self.logger.info("MCP Orchestrator Starting...")
        self.logger.info("=" * 80)
        
        # Initialize components
        self._initialize_components()
        
    def _initialize_components(self):
        """Initialize all pipeline components"""
        self.logger.info("Initializing components...")
        
        # Storage
        self.db = DatabaseManager(self.config)
        self.index = IndexManager(self.config, self.logger)
        
        # Discovery & Scraping
        self.discovery = DiscoveryManager(self.config, self.logger)
        self.scraper = ScraperManager(self.config, self.logger)
        
        # Processing
        self.extractor = ExtractorManager(self.config, self.logger)
        self.deduplicator = Deduplicator(self.config, self.logger)
        self.scorer = RelevanceScorer(self.config, self.logger)
        
        # AI Agents
        self.summarizer = SummarizerAgent(self.config, self.logger)
        self.headline_gen = HeadlineGenerator(self.config, self.logger)
        
        # Generation
        self.newspaper_gen = NewspaperGenerator(self.config, self.logger)
        
        # Notifications
        self.notifier = Notifier(self.config, self.logger)
        
        self.logger.info("All components initialized successfully")
        
    def run_pipeline(self, topics: List[str] = None, date: str = None, max_items: int = 100):
        """
        Run the complete pipeline
        
        Args:
            topics: List of topics to search for (default: from config)
            date: Date to run for (default: today)
            max_items: Maximum items to process
        """
        start_time = datetime.now()
        
        # Use config topics if not provided
        if topics is None:
            topics = self.config.get('topics', [])
        
        # Use today if date not provided
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        self.logger.info(f"Running pipeline for topics: {topics}")
        self.logger.info(f"Date: {date}")
        self.logger.info(f"Max items: {max_items}")
        
        try:
            # Step 1: Discovery
            self.logger.info("\n" + "="*60)
            self.logger.info("STEP 1: DISCOVERY")
            self.logger.info("="*60)
            candidates = self.discovery.discover_all(topics, date)
            self.logger.info(f"Discovered {len(candidates)} candidate items")
            
            if not candidates:
                self.logger.warning("No candidates found. Exiting.")
                return None
            
            # Step 2: Fetch & Scrape
            self.logger.info("\n" + "="*60)
            self.logger.info("STEP 2: FETCH & SCRAPE")
            self.logger.info("="*60)
            scraped_items = self.scraper.scrape_batch(candidates[:max_items])
            self.logger.info(f"Successfully scraped {len(scraped_items)} items")
            
            # Step 3: Extract & Process
            self.logger.info("\n" + "="*60)
            self.logger.info("STEP 3: EXTRACT & PROCESS")
            self.logger.info("="*60)
            extracted_items = self.extractor.extract_batch(scraped_items)
            self.logger.info(f"Extracted content from {len(extracted_items)} items")
            
            # Step 4: Deduplicate
            self.logger.info("\n" + "="*60)
            self.logger.info("STEP 4: DEDUPLICATION")
            self.logger.info("="*60)
            unique_items = self.deduplicator.deduplicate(extracted_items)
            self.logger.info(f"After deduplication: {len(unique_items)} unique items")
            
            # Step 5: Score & Rank
            self.logger.info("\n" + "="*60)
            self.logger.info("STEP 5: SCORING & RANKING")
            self.logger.info("="*60)
            scored_items = self.scorer.score_and_rank(unique_items, topics)
            self.logger.info(f"Scored and ranked {len(scored_items)} items")
            
            # Step 6: Summarize
            self.logger.info("\n" + "="*60)
            self.logger.info("STEP 6: SUMMARIZATION")
            self.logger.info("="*60)
            summarized_items = self.summarizer.summarize_batch(scored_items)
            self.logger.info(f"Generated summaries for {len(summarized_items)} items")
            
            # Step 7: Generate Headlines
            self.logger.info("\n" + "="*60)
            self.logger.info("STEP 7: HEADLINE GENERATION")
            self.logger.info("="*60)
            final_items = self.headline_gen.generate_headlines(summarized_items)
            self.logger.info(f"Generated headlines for {len(final_items)} items")
            
            # Step 8: Generate Newspaper
            self.logger.info("\n" + "="*60)
            self.logger.info("STEP 8: NEWSPAPER GENERATION")
            self.logger.info("="*60)
            newspaper = self.newspaper_gen.generate(
                items=final_items,
                topics=topics,
                date=date
            )
            
            # Step 9: Save to Database & Index
            self.logger.info("\n" + "="*60)
            self.logger.info("STEP 9: STORAGE")
            self.logger.info("="*60)
            self.db.save_items(final_items)
            self.index.add_items(final_items)
            self.logger.info("Saved to database and search index")
            
            # Step 10: Notify
            if self.config.get('notifications', {}).get('enabled', False):
                self.notifier.send_notification(
                    title=f"Daily Newspaper Generated - {date}",
                    message=f"Successfully generated newspaper with {len(final_items)} items",
                    newspaper_path=newspaper['paths']['html']
                )
            
            # Log summary
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            self.logger.info("\n" + "="*80)
            self.logger.info("PIPELINE COMPLETED SUCCESSFULLY")
            self.logger.info("="*80)
            self.logger.info(f"Duration: {duration:.2f} seconds")
            self.logger.info(f"Items processed: {len(final_items)}")
            self.logger.info(f"Newspaper saved to: {newspaper['paths']['html']}")
            self.logger.info("="*80)
            
            return newspaper
            
        except Exception as e:
            self.logger.error(f"Pipeline failed: {str(e)}", exc_info=True)
            
            # Send error notification
            if self.config.get('notifications', {}).get('enabled', False):
                self.notifier.send_notification(
                    title=f"Pipeline Failed - {date}",
                    message=f"Error: {str(e)}",
                    is_error=True
                )
            
            raise
            
    def run_scheduled(self):
        """Run the pipeline on a schedule"""
        from apscheduler.schedulers.blocking import BlockingScheduler
        from apscheduler.triggers.cron import CronTrigger
        
        scheduler = BlockingScheduler()
        
        # Parse cron expression from config
        cron_expr = self.config.get('schedule', {}).get('cron', '0 2 * * *')
        
        # Split cron expression (minute hour day month day_of_week)
        parts = cron_expr.split()
        trigger = CronTrigger(
            minute=parts[0],
            hour=parts[1],
            day=parts[2] if len(parts) > 2 else '*',
            month=parts[3] if len(parts) > 3 else '*',
            day_of_week=parts[4] if len(parts) > 4 else '*'
        )
        
        scheduler.add_job(
            self.run_pipeline,
            trigger=trigger,
            id='mcp_daily_run',
            name='MCP Daily Research Newspaper'
        )
        
        self.logger.info(f"Scheduler started with cron: {cron_expr}")
        self.logger.info("Press Ctrl+C to exit")
        
        try:
            scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            self.logger.info("Scheduler stopped")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='MCP Server - Daily Research + News Newspaper Generator'
    )
    
    parser.add_argument(
        '--config',
        default='config/config.yaml',
        help='Path to configuration file'
    )
    
    parser.add_argument(
        '--topics',
        nargs='+',
        help='Topics to search for (overrides config)'
    )
    
    parser.add_argument(
        '--date',
        help='Date to run for (YYYY-MM-DD, default: today)'
    )
    
    parser.add_argument(
        '--max-items',
        type=int,
        default=100,
        help='Maximum items to process'
    )
    
    parser.add_argument(
        '--schedule',
        action='store_true',
        help='Run on schedule (from config)'
    )
    
    parser.add_argument(
        '--backfill',
        type=int,
        help='Backfill N days of data'
    )
    
    args = parser.parse_args()
    
    # Initialize orchestrator
    orchestrator = MCPOrchestrator(config_path=args.config)
    
    if args.schedule:
        # Run on schedule
        orchestrator.run_scheduled()
    elif args.backfill:
        # Backfill mode
        for i in range(args.backfill):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            print(f"\nBackfilling {date}...")
            orchestrator.run_pipeline(
                topics=args.topics,
                date=date,
                max_items=args.max_items
            )
    else:
        # Single run
        orchestrator.run_pipeline(
            topics=args.topics,
            date=args.date,
            max_items=args.max_items
        )


if __name__ == '__main__':
    main()
