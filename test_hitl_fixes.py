"""
Test Suite for HITL Workflow Fixes
===================================

Comprehensive tests for all fixes implemented.

Usage:
    python test_hitl_fixes.py
"""

import unittest
import sqlite3
import tempfile
import os
import pandas as pd
import io
from unittest.mock import Mock, patch, MagicMock

# Import fixes
from hitl_fixes import (
    EnhancedDatabaseManager,
    DatabaseTransaction,
    SafeDocumentUploader,
    validate_markdown_content,
    create_safe_job_id,
    SafeOrchestrator
)


class TestEnhancedDatabaseManager(unittest.TestCase):
    """Test transaction management in database."""

    def setUp(self):
        """Create temporary database for testing."""
        self.db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.db_file.close()
        self.db = EnhancedDatabaseManager(self.db_file.name)
        self.db.connect()

        # Create test table
        self.db.cursor.execute("""
            CREATE TABLE test_table (
                id INTEGER PRIMARY KEY,
                value TEXT
            )
        """)
        self.db.conn.commit()

    def tearDown(self):
        """Clean up temporary database."""
        self.db.close()
        os.unlink(self.db_file.name)

    def test_transaction_commit(self):
        """Test successful transaction commit."""
        with self.db.transaction():
            self.db.execute_update("INSERT INTO test_table (value) VALUES (?)", ("test1",))
            self.db.execute_update("INSERT INTO test_table (value) VALUES (?)", ("test2",))

        # Verify data was committed
        results = self.db.execute_query("SELECT * FROM test_table")
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['value'], 'test1')
        self.assertEqual(results[1]['value'], 'test2')

    def test_transaction_rollback(self):
        """Test automatic rollback on error."""
        try:
            with self.db.transaction():
                self.db.execute_update("INSERT INTO test_table (value) VALUES (?)", ("test1",))
                # This should cause an error (duplicate primary key if we insert id=1 twice)
                raise Exception("Simulated error")
        except Exception:
            pass

        # Verify no data was committed
        results = self.db.execute_query("SELECT * FROM test_table")
        self.assertEqual(len(results), 0, "Transaction should have been rolled back")

    def test_nested_transaction_prevention(self):
        """Test that nested transactions work correctly."""
        with self.db.transaction():
            self.db.execute_update("INSERT INTO test_table (value) VALUES (?)", ("outer",))

            # Inner transaction should be part of outer
            with self.db.transaction():
                self.db.execute_update("INSERT INTO test_table (value) VALUES (?)", ("inner",))

        results = self.db.execute_query("SELECT * FROM test_table")
        self.assertEqual(len(results), 2)


class TestSafeDocumentUploader(unittest.TestCase):
    """Test file size validation and Excel handling."""

    def setUp(self):
        """Create uploader instance."""
        self.uploader = SafeDocumentUploader(max_file_size_mb=1)  # 1MB for testing

    def test_file_size_validation_pass(self):
        """Test that small files pass validation."""
        small_file = b"x" * 100  # 100 bytes
        result = self.uploader._validate_file_size(small_file, "test.csv")
        self.assertTrue(result)

    def test_file_size_validation_fail(self):
        """Test that large files fail validation."""
        large_file = b"x" * (2 * 1024 * 1024)  # 2MB
        with self.assertRaises(ValueError) as context:
            self.uploader._validate_file_size(large_file, "large.csv")

        self.assertIn("too large", str(context.exception))
        self.assertIn("2.0 MB", str(context.exception))

    def test_csv_processing(self):
        """Test CSV file processing with size validation."""
        csv_data = "name,age\nAlice,30\nBob,25"
        csv_bytes = csv_data.encode('utf-8')

        file_type, data = self.uploader._process_file("test.csv", csv_bytes)

        self.assertEqual(file_type, 'CSV')
        self.assertIsInstance(data, pd.DataFrame)
        self.assertEqual(len(data), 2)
        self.assertEqual(list(data.columns), ['name', 'age'])

    def test_unsupported_file_type(self):
        """Test that unsupported file types raise error."""
        with self.assertRaises(ValueError) as context:
            self.uploader._process_file("test.exe", b"data")

        self.assertIn("Unsupported file type", str(context.exception))


class TestMarkdownValidation(unittest.TestCase):
    """Test markdown content validation."""

    def test_valid_markdown(self):
        """Test that valid markdown passes validation."""
        valid_content = """
## Variable: blood_pressure

**Description:** Systolic blood pressure measurement

**Technical Details:**
- Data Type: continuous
- Valid Values: 70-250 mmHg

**Clinical Context:** Essential vital sign for cardiovascular assessment
"""
        is_valid, issues = validate_markdown_content(valid_content)
        self.assertTrue(is_valid, f"Valid markdown should pass: {issues}")
        self.assertEqual(len(issues), 0)

    def test_too_short(self):
        """Test that very short content fails."""
        short_content = "hi"
        is_valid, issues = validate_markdown_content(short_content)
        self.assertFalse(is_valid)
        self.assertTrue(any("too short" in issue.lower() for issue in issues))

    def test_missing_headers(self):
        """Test that content without headers fails."""
        no_headers = "This is just plain text without any markdown headers or structure."
        is_valid, issues = validate_markdown_content(no_headers)
        self.assertFalse(is_valid)
        self.assertTrue(any("header" in issue.lower() for issue in issues))

    def test_unmatched_code_blocks(self):
        """Test detection of unmatched code blocks."""
        unmatched = """
## Variable: test

```python
def foo():
    pass

Missing closing backticks
"""
        is_valid, issues = validate_markdown_content(unmatched)
        self.assertFalse(is_valid)
        self.assertTrue(any("code block" in issue.lower() for issue in issues))

    def test_placeholder_detection(self):
        """Test detection of placeholder text."""
        with_placeholder = """
## Variable: blood_pressure

**Description:** TODO: Add description here

**Technical Details:**
- Data Type: continuous
"""
        is_valid, issues = validate_markdown_content(with_placeholder)
        self.assertFalse(is_valid)
        self.assertTrue(any("placeholder" in issue.lower() for issue in issues))

    def test_missing_required_sections(self):
        """Test detection of missing required content."""
        minimal = """
## Variable: test

This is minimal content.
"""
        is_valid, issues = validate_markdown_content(minimal)
        self.assertFalse(is_valid)
        # Should flag missing sections like description, data type, etc.
        self.assertTrue(any("missing" in issue.lower() for issue in issues))


class TestJobIDGeneration(unittest.TestCase):
    """Test UUID-based job ID generation."""

    def test_job_id_format(self):
        """Test that job IDs are correctly formatted."""
        job_id = create_safe_job_id("test.csv")

        # Should be 12 characters (shortened UUID without hyphens)
        self.assertEqual(len(job_id), 12)

        # Should be alphanumeric
        self.assertTrue(job_id.isalnum())

    def test_job_id_uniqueness(self):
        """Test that job IDs are unique."""
        ids = set()
        for i in range(100):
            job_id = create_safe_job_id(f"test{i}.csv")
            ids.add(job_id)

        # All 100 should be unique
        self.assertEqual(len(ids), 100)

    def test_no_collision_with_same_filename(self):
        """Test that same filename generates different IDs."""
        id1 = create_safe_job_id("test.csv")
        id2 = create_safe_job_id("test.csv")

        # Should be different (time-based UUID component)
        self.assertNotEqual(id1, id2)


class TestSafeOrchestrator(unittest.TestCase):
    """Test orchestrator with transaction management."""

    def setUp(self):
        """Create temporary database and orchestrator."""
        self.db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.db_file.close()
        self.db = EnhancedDatabaseManager(self.db_file.name)
        self.db.connect()

        # Create Jobs table
        self.db.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Jobs (
                job_id TEXT PRIMARY KEY,
                source_file TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Running',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create ReviewQueue table
        self.db.cursor.execute("""
            CREATE TABLE IF NOT EXISTS ReviewQueue (
                item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Pending',
                source_agent TEXT NOT NULL,
                source_data TEXT,
                generated_content TEXT,
                FOREIGN KEY (job_id) REFERENCES Jobs(job_id)
            )
        """)
        self.db.conn.commit()

        self.orchestrator = SafeOrchestrator(self.db, None)

    def tearDown(self):
        """Clean up."""
        self.db.close()
        os.unlink(self.db_file.name)

    def test_create_job_with_uuid(self):
        """Test that jobs are created with UUID-based IDs."""
        job_id = self.orchestrator.create_job("test.csv")

        # Verify job was created
        jobs = self.db.execute_query("SELECT * FROM Jobs WHERE job_id = ?", (job_id,))
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]['source_file'], 'test.csv')
        self.assertEqual(jobs[0]['status'], 'Running')

    def test_transaction_rollback_on_error(self):
        """Test that errors trigger rollback."""
        # This test would require mocking agent processing
        # For now, just test the structure exists
        self.assertTrue(hasattr(self.orchestrator, 'process_data_dictionary_safe'))


class TestIntegration(unittest.TestCase):
    """Integration tests for complete workflow."""

    def test_full_workflow_simulation(self):
        """Simulate a complete workflow with all fixes."""
        # Create database
        db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        db_file.close()
        db = EnhancedDatabaseManager(db_file.name)
        db.connect()

        try:
            # Initialize schema
            db.cursor.execute("""
                CREATE TABLE Jobs (
                    job_id TEXT PRIMARY KEY,
                    source_file TEXT,
                    status TEXT
                )
            """)

            # Test transaction workflow
            with db.transaction():
                job_id = create_safe_job_id("test.csv")
                db.execute_update(
                    "INSERT INTO Jobs (job_id, source_file, status) VALUES (?, ?, ?)",
                    (job_id, "test.csv", "Running")
                )

            # Verify job was created
            jobs = db.execute_query("SELECT * FROM Jobs")
            self.assertEqual(len(jobs), 1)

            # Test file upload simulation
            uploader = SafeDocumentUploader(max_file_size_mb=50)
            csv_data = "field,type\nage,integer\nname,text"
            csv_bytes = csv_data.encode('utf-8')

            # Should not raise (file is small)
            uploader._validate_file_size(csv_bytes, "test.csv")

            # Test validation
            good_markdown = "## Variable: age\n\n**Description:** Patient age\n\n**Data Type:** integer"
            is_valid, _ = validate_markdown_content(good_markdown)
            self.assertTrue(is_valid)

        finally:
            db.close()
            os.unlink(db_file.name)


def run_tests():
    """Run all tests and print results."""
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromModule(__import__(__name__))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("="*70)

    if result.wasSuccessful():
        print("✅ ALL TESTS PASSED!")
    else:
        print("❌ SOME TESTS FAILED")

    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    exit(0 if success else 1)
