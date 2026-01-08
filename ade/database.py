import sqlite3
import json
import logging
from typing import List, Dict, Optional, Any

logger = logging.getLogger('ADE.Database')

class DatabaseManager:
    """
    Manages SQLite database operations with session and memory support.
    Enhanced with transaction management.
    """

    def __init__(self, db_path: str = "project.db"):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self._in_transaction = False

    def connect(self):
        """Establish database connection."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        logger.info(f"Connected to database: {self.db_path}")

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")

    def begin_transaction(self):
        """Begin a transaction."""
        if not self._in_transaction:
            self.conn.execute("BEGIN")
            self._in_transaction = True
            logger.debug("Transaction started")

    def commit_transaction(self):
        """Commit the current transaction."""
        if self._in_transaction:
            self.conn.commit()
            self._in_transaction = False
            logger.debug("Transaction committed")

    def rollback_transaction(self):
        """Rollback the current transaction."""
        if self._in_transaction:
            self.conn.rollback()
            self._in_transaction = False
            logger.warning("Transaction rolled back")

    def transaction(self):
        """Context manager for transactions."""
        return DatabaseTransaction(self)

    def execute_query(self, query: str, params: tuple = ()) -> List[Dict]:
        """Execute SELECT query and return results."""
        self.cursor.execute(query, params)
        rows = self.cursor.fetchall()
        return [dict(row) for row in rows]

    def execute_update(self, query: str, params: tuple = ()) -> int:
        """Execute INSERT/UPDATE/DELETE and return affected row ID."""
        self.cursor.execute(query, params)
        if not self._in_transaction:
            self.conn.commit()
        return self.cursor.lastrowid

    def initialize_schema(self):
        """Create all required tables."""

        # Agents table
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS Agents (
            agent_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            system_prompt TEXT NOT NULL,
            agent_type TEXT NOT NULL,
            config JSON,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Snippets table - Named context storage
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS Snippets (
            snippet_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            snippet_type TEXT NOT NULL CHECK(snippet_type IN (
                'Summary', 'Chunk', 'Instruction', 'Version', 'Design', 'Mapping',
                'Convention', 'Changelog', 'Instrument', 'Segment', 'Glossary'
            )),
            content TEXT NOT NULL,
            metadata JSON,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Jobs table with enhanced metadata
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS Jobs (
            job_id TEXT PRIMARY KEY,
            source_file TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Running' CHECK(status IN (
                'Running', 'Completed', 'Failed', 'Paused'
            )),
            metadata JSON,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # ReviewQueue table - HITL workflow
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS ReviewQueue (
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending' CHECK(status IN (
                'Pending', 'Approved', 'Rejected', 'Needs_Clarification'
            )),
            source_agent TEXT NOT NULL,
            target_agent TEXT,
            source_data TEXT NOT NULL,
            generated_content TEXT NOT NULL,
            approved_content TEXT,
            rejection_feedback TEXT,
            clarification_response TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_id) REFERENCES Jobs(job_id)
        )
        """)

        # Sessions table - ADK-style session management
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS Sessions (
            session_id TEXT PRIMARY KEY,
            job_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            state JSON DEFAULT '{}',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_id) REFERENCES Jobs(job_id)
        )
        """)

        # SessionHistory - Conversation history
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS SessionHistory (
            history_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            job_id TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system', 'tool')),
            content TEXT NOT NULL,
            metadata JSON,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES Sessions(session_id),
            FOREIGN KEY (job_id) REFERENCES Jobs(job_id)
        )
        """)

        # Memory table - Long-term knowledge storage
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS Memory (
            memory_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            content TEXT NOT NULL,
            embedding JSON,
            metadata JSON,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # SystemState table
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS SystemState (
            state_key TEXT PRIMARY KEY,
            state_value TEXT NOT NULL,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)

        self.conn.commit()
        logger.info("Database schema initialized with session and memory support")


class DatabaseTransaction:
    """Context manager for database transactions."""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def __enter__(self):
        self.db.begin_transaction()
        return self.db

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            # Error occurred, rollback
            self.db.rollback_transaction()
            logger.error(f"Transaction rolled back due to error: {exc_val}")
            return False  # Re-raise the exception
        else:
            # Success, commit
            self.db.commit_transaction()
            return True

# Alias for backward compatibility
EnhancedDatabaseManager = DatabaseManager
