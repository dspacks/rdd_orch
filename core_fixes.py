"""
Core fixes for critical issues in ADE Healthcare Documentation System.

This module provides:
1. Environment-agnostic API configuration with fallback authentication
2. Safe database operations with transaction safety
3. Robust JSON parsing for LLM outputs
4. API key validation
"""

import os
import json
import logging
import sqlite3
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# 1. FIX: Environment-Agnostic API Configuration
# ============================================================================

def get_api_key_with_fallback() -> str:
    """
    Get Google API key with environment-agnostic fallback.

    Tries in order:
    1. Google Colab userdata (if in Colab)
    2. Kaggle secrets (if in Kaggle)
    3. Environment variable GOOGLE_API_KEY
    4. Environment variable GEMINI_API_KEY

    Returns:
        str: The API key

    Raises:
        ValueError: If no API key found in any location
    """
    api_key = None

    # Try Google Colab
    try:
        from google.colab import userdata
        api_key = userdata.get('GOOGLE_API_KEY')
        logger.info("✓ API key loaded from Google Colab secrets")
        return api_key
    except ImportError:
        pass
    except Exception as e:
        logger.debug(f"Colab userdata not available: {e}")

    # Try Kaggle
    try:
        from kaggle_secrets import UserSecretsClient
        user_secrets = UserSecretsClient()
        api_key = user_secrets.get_secret("GOOGLE_API_KEY")
        logger.info("✓ API key loaded from Kaggle secrets")
        return api_key
    except ImportError:
        pass
    except Exception as e:
        logger.debug(f"Kaggle secrets not available: {e}")

    # Try environment variables
    api_key = os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')
    if api_key:
        logger.info("✓ API key loaded from environment variable")
        return api_key

    # No API key found
    raise ValueError(
        "GOOGLE_API_KEY not found. Please set it in one of:\n"
        "  - Google Colab: Add to Secrets\n"
        "  - Kaggle: Add to Secrets\n"
        "  - Environment: export GOOGLE_API_KEY='your-key'\n"
        "  - .env file: GOOGLE_API_KEY=your-key"
    )


def validate_api_key(api_key: str) -> bool:
    """
    Validate that the API key works by making a test call.

    Args:
        api_key: The API key to validate

    Returns:
        bool: True if valid, False otherwise
    """
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)

        # Make a minimal test call
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        response = model.generate_content("Hello")

        logger.info("✓ API key validated successfully")
        return True
    except Exception as e:
        logger.error(f"✗ API key validation failed: {e}")
        return False


def configure_gemini_api() -> str:
    """
    Configure Gemini API with environment-agnostic authentication and validation.

    Returns:
        str: The validated API key

    Raises:
        ValueError: If API key cannot be found or validated
    """
    import google.generativeai as genai

    # Get API key with fallback
    api_key = get_api_key_with_fallback()

    # Configure API
    genai.configure(api_key=api_key)

    # Validate (optional but recommended)
    # Commented out to avoid unnecessary API call on every import
    # if not validate_api_key(api_key):
    #     raise ValueError("API key validation failed")

    logger.info("✓ Gemini API configured successfully")
    return api_key


# ============================================================================
# 2. FIX: Safe Database Operations with Transaction Safety
# ============================================================================

class SafeDatabaseManager:
    """
    Enhanced DatabaseManager with transaction safety and proper error handling.

    Improvements:
    - Connection timeout to prevent indefinite locks
    - Foreign key constraint enforcement
    - Transaction rollback on errors
    - Proper exception handling
    - Context manager support
    """

    def __init__(self, db_path: str = "project.db", timeout: float = 30.0):
        """
        Initialize database manager.

        Args:
            db_path: Path to SQLite database file
            timeout: Connection timeout in seconds (default: 30.0)
        """
        self.db_path = db_path
        self.timeout = timeout
        self.conn = None
        self.cursor = None

    def connect(self):
        """Establish database connection with timeout and foreign key enforcement."""
        try:
            self.conn = sqlite3.connect(self.db_path, timeout=self.timeout)
            self.conn.row_factory = sqlite3.Row
            self.cursor = self.conn.cursor()

            # Enable foreign key constraints (not enabled by default in SQLite)
            self.cursor.execute("PRAGMA foreign_keys = ON")

            logger.info(f"✓ Database connected: {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"✗ Database connection failed: {e}")
            raise

    def close(self):
        """Close database connection."""
        if self.conn:
            try:
                self.conn.close()
                logger.debug("Database connection closed")
            except sqlite3.Error as e:
                logger.error(f"Error closing database: {e}")

    def execute_query(self, query: str, params: tuple = ()) -> List[Dict]:
        """
        Execute SELECT query and return results.

        Args:
            query: SQL query string
            params: Query parameters (optional)

        Returns:
            List of dictionaries representing rows
        """
        try:
            self.cursor.execute(query, params)
            rows = self.cursor.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Query execution failed: {e}")
            logger.debug(f"Query: {query}")
            logger.debug(f"Params: {params}")
            raise

    def execute_update(self, query: str, params: tuple = ()) -> int:
        """
        Execute INSERT/UPDATE/DELETE with transaction safety.

        Args:
            query: SQL query string
            params: Query parameters (optional)

        Returns:
            ID of last inserted/updated row

        Raises:
            sqlite3.Error: On database errors (after rollback)
        """
        try:
            self.cursor.execute(query, params)
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.Error as e:
            logger.error(f"Update execution failed: {e}")
            logger.debug(f"Query: {query}")
            logger.debug(f"Params: {params}")

            # Rollback transaction on error
            try:
                self.conn.rollback()
                logger.info("✓ Transaction rolled back")
            except sqlite3.Error as rollback_error:
                logger.error(f"✗ Rollback failed: {rollback_error}")

            raise

    def execute_many(self, query: str, params_list: List[tuple]) -> int:
        """
        Execute multiple INSERT/UPDATE/DELETE statements in a single transaction.

        Args:
            query: SQL query string
            params_list: List of parameter tuples

        Returns:
            Number of rows affected
        """
        try:
            self.cursor.executemany(query, params_list)
            self.conn.commit()
            return self.cursor.rowcount
        except sqlite3.Error as e:
            logger.error(f"Batch execution failed: {e}")

            try:
                self.conn.rollback()
                logger.info("✓ Transaction rolled back")
            except sqlite3.Error as rollback_error:
                logger.error(f"✗ Rollback failed: {rollback_error}")

            raise

    def safe_schema_migration(self, drop_table: str, create_table_sql: str,
                             copy_data_sql: Optional[str] = None) -> bool:
        """
        Safely migrate schema with savepoint and rollback capability.

        Args:
            drop_table: Name of table to drop
            create_table_sql: SQL to create new table
            copy_data_sql: Optional SQL to copy data from old to new

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create savepoint
            self.cursor.execute("SAVEPOINT schema_migration")

            # Check if table exists
            table_check = self.execute_query(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (drop_table,)
            )

            if table_check:
                # Backup old table
                backup_table = f"{drop_table}_backup_{int(time.time())}"
                self.cursor.execute(f"ALTER TABLE {drop_table} RENAME TO {backup_table}")
                logger.info(f"✓ Backed up {drop_table} to {backup_table}")

            # Create new table
            self.cursor.execute(create_table_sql)
            logger.info(f"✓ Created new table structure")

            # Copy data if provided
            if copy_data_sql and table_check:
                self.cursor.execute(copy_data_sql)
                logger.info(f"✓ Copied data to new table")

            # Commit migration
            self.conn.commit()
            self.cursor.execute("RELEASE SAVEPOINT schema_migration")
            logger.info("✓ Schema migration completed successfully")

            return True

        except sqlite3.Error as e:
            logger.error(f"✗ Schema migration failed: {e}")

            try:
                self.cursor.execute("ROLLBACK TO SAVEPOINT schema_migration")
                self.cursor.execute("RELEASE SAVEPOINT schema_migration")
                logger.info("✓ Migration rolled back to savepoint")
            except sqlite3.Error as rollback_error:
                logger.error(f"✗ Rollback failed: {rollback_error}")

            return False

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with automatic cleanup."""
        if exc_type is not None:
            # Error occurred, rollback if possible
            if self.conn:
                try:
                    self.conn.rollback()
                    logger.info("✓ Transaction rolled back due to exception")
                except sqlite3.Error:
                    pass
        self.close()
        return False


# ============================================================================
# 3. FIX: Safe JSON Parsing for LLM Outputs
# ============================================================================

def safe_parse_json(
    result: str,
    default: Optional[Dict] = None,
    strict: bool = False
) -> Dict[str, Any]:
    """
    Safely parse JSON from LLM response with multiple fallback strategies.

    Args:
        result: LLM response string (may contain JSON in code blocks)
        default: Default value to return on parse failure (if not strict)
        strict: If True, raise exception on parse failure

    Returns:
        Parsed JSON dictionary

    Raises:
        json.JSONDecodeError: If strict=True and parsing fails
    """
    default = default or {}

    # Strategy 1: Try parsing as-is
    try:
        return json.loads(result)
    except json.JSONDecodeError:
        pass

    # Strategy 2: Extract from ```json code blocks
    if "```json" in result:
        try:
            json_str = result.split("```json")[1].split("```")[0].strip()
            return json.loads(json_str)
        except (json.JSONDecodeError, IndexError) as e:
            logger.debug(f"Failed to parse JSON from code block: {e}")

    # Strategy 3: Extract from any ``` code blocks
    if "```" in result:
        try:
            parts = result.split("```")
            # Try each code block
            for i in range(1, len(parts), 2):
                code_block = parts[i]
                # Remove language identifier if present
                lines = code_block.strip().split('\n')
                if lines and lines[0].lower() in ['json', 'javascript', 'js']:
                    code_block = '\n'.join(lines[1:])
                try:
                    return json.loads(code_block)
                except json.JSONDecodeError:
                    continue
        except Exception as e:
            logger.debug(f"Failed to extract from code blocks: {e}")

    # Strategy 4: Find JSON-like structure with regex
    import re
    json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
    matches = re.findall(json_pattern, result)
    for match in matches:
        try:
            return json.loads(match)
        except json.JSONDecodeError:
            continue

    # All strategies failed
    logger.warning(f"Failed to parse JSON from response")
    logger.debug(f"Response preview: {result[:200]}...")

    if strict:
        raise json.JSONDecodeError(
            "Could not extract valid JSON from LLM response",
            result,
            0
        )

    return default


def extract_json_or_text(result: str) -> tuple[Optional[Dict], str]:
    """
    Extract both JSON content and remaining text from LLM response.

    Useful when LLM returns both structured data and explanatory text.

    Args:
        result: LLM response string

    Returns:
        Tuple of (parsed_json or None, remaining_text)
    """
    try:
        parsed = safe_parse_json(result, default=None, strict=False)
        if parsed:
            # Remove JSON portion from text
            remaining = result
            for marker in ["```json", "```"]:
                if marker in remaining:
                    parts = remaining.split(marker)
                    if len(parts) >= 3:
                        remaining = parts[0] + parts[2]
            return parsed, remaining.strip()
    except Exception:
        pass

    return None, result


# ============================================================================
# Utility: Time import for schema migration
# ============================================================================

import time

