"""Database Manager - SQLite/PostgreSQL storage"""

from typing import Dict, Any, List
import logging
from pathlib import Path
import json


class DatabaseManager:
    """Manages database operations"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize database manager
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        
        db_config = config.get('storage', {}).get('database', {})
        db_type = db_config.get('type', 'sqlite')
        
        if db_type == 'sqlite':
            self._init_sqlite(db_config)
        elif db_type == 'postgresql':
            self._init_postgresql(db_config)
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
    
    def _init_sqlite(self, db_config: Dict[str, Any]):
        """Initialize SQLite database"""
        import sqlite3
        
        db_path = db_config.get('path', './data/mcp.db')
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        
        # Create tables
        self._create_tables()
    
    def _init_postgresql(self, db_config: Dict[str, Any]):
        """Initialize PostgreSQL database"""
        import psycopg2
        from psycopg2.extras import RealDictCursor
        
        self.conn = psycopg2.connect(
            host=db_config.get('host', 'localhost'),
            port=db_config.get('port', 5432),
            database=db_config.get('database', 'mcp_research'),
            user=db_config.get('user', ''),
            password=db_config.get('password', ''),
            cursor_factory=RealDictCursor
        )
        
        self._create_tables()
    
    def _create_tables(self):
        """Create database tables"""
        cursor = self.conn.cursor()
        
        # Items table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id TEXT PRIMARY KEY,
                url TEXT,
                title TEXT,
                authors TEXT,
                abstract TEXT,
                published_at TEXT,
                source TEXT,
                type TEXT,
                doi TEXT,
                score REAL,
                data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Newspapers table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS newspapers (
                date TEXT PRIMARY KEY,
                topics TEXT,
                data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.conn.commit()
    
    def save_items(self, items: List[Dict[str, Any]]):
        """Save items to database"""
        cursor = self.conn.cursor()
        
        for item in items:
            cursor.execute("""
                INSERT OR REPLACE INTO items 
                (id, url, title, authors, abstract, published_at, source, type, doi, score, data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item.get('id', ''),
                item.get('url', ''),
                item.get('title', ''),
                json.dumps(item.get('authors', [])),
                item.get('abstract', ''),
                item.get('published_at', ''),
                item.get('source', ''),
                item.get('type', ''),
                item.get('doi', ''),
                item.get('score', 0.0),
                json.dumps(item)
            ))
        
        self.conn.commit()
    
    def get_item(self, item_id: str) -> Dict[str, Any]:
        """Get item by ID"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT data FROM items WHERE id = ?", (item_id,))
        row = cursor.fetchone()
        
        if row:
            return json.loads(row[0])
        return None
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()


class IndexManager:
    """Manages search indexing (simple in-memory for now)"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize index manager"""
        self.config = config
        self.index = {}
    
    def index_items(self, items: List[Dict[str, Any]]):
        """Index items"""
        for item in items:
            item_id = item.get('id')
            if item_id:
                self.index[item_id] = item
    
    def search(self, query: str) -> List[Dict[str, Any]]:
        """Simple search"""
        results = []
        query_lower = query.lower()
        
        for item in self.index.values():
            text = f"{item.get('title', '')} {item.get('abstract', '')}".lower()
            if query_lower in text:
                results.append(item)
        
        return results
