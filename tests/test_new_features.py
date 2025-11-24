"""
Tests for New Features Implementation

Tests all features from features_implementation.py:
1. Field-level comments system
2. Quality score display
3. Excel export functionality
4. Version comparison UI
5. Template library
"""

import pytest
import sqlite3
import pandas as pd
import json
import os
from datetime import datetime
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from features_implementation import (
    CommentsManager,
    QualityScoreCalculator,
    QualityMetrics,
    ExcelExporter,
    VersionComparisonWidget,
    TemplateLibrary
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    db_path = "test_features.db"

    # Create database connection
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Create minimal schema
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ReviewQueue (
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT NOT NULL,
            source_agent TEXT NOT NULL,
            source_data TEXT NOT NULL,
            generated_content TEXT NOT NULL,
            approved_content TEXT,
            status TEXT DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Mock database manager
    class MockDB:
        def __init__(self, conn):
            self.conn = conn
            self.cursor = conn.cursor()

        def execute_query(self, query, params=()):
            self.cursor.execute(query, params)
            rows = self.cursor.fetchall()
            return [dict(row) for row in rows]

        def execute_update(self, query, params=()):
            self.cursor.execute(query, params)
            self.conn.commit()
            return self.cursor.lastrowid

    db = MockDB(conn)

    yield db

    # Cleanup
    conn.close()
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture
def sample_documentation():
    """Sample documentation content for testing."""
    return """## Variable: blood_pressure_systolic

**Description:** Systolic blood pressure measurement taken during clinic visit

**Data Type:** Integer

**Valid Range:** 70-250 mmHg

**Units:** mmHg

**Ontology Mappings:**
- LOINC: 8480-6 (Systolic blood pressure)
- OMOP Concept: 3004249 (Systolic blood pressure)
- SNOMED CT: 271649006 (Systolic blood pressure)

**Clinical Context:**
Blood pressure is a key vital sign used to assess cardiovascular health.

**Example Values:**
- 120 mmHg (normal)
- 140 mmHg (stage 1 hypertension)
"""


# ============================================================================
# TEST FEATURE 1: FIELD-LEVEL COMMENTS
# ============================================================================

def test_comments_manager_initialization(temp_db):
    """Test CommentsManager initialization and table creation."""
    comments_mgr = CommentsManager(temp_db)

    # Check table was created
    query = "SELECT name FROM sqlite_master WHERE type='table' AND name='FieldComments'"
    result = temp_db.execute_query(query)

    assert len(result) == 1
    assert result[0]['name'] == 'FieldComments'


def test_add_comment(temp_db):
    """Test adding a comment."""
    comments_mgr = CommentsManager(temp_db)

    # First add a review item
    temp_db.execute_update("""
        INSERT INTO ReviewQueue (job_id, source_agent, source_data, generated_content)
        VALUES (?, ?, ?, ?)
    """, ("job-123", "TestAgent", "{}", "test content"))

    item_id = 1

    # Add comment
    comment_id = comments_mgr.add_comment(
        item_id,
        "Dr. Smith",
        "This needs clarification about the units",
        "question"
    )

    assert comment_id > 0

    # Retrieve comment
    comments = comments_mgr.get_comments(item_id)
    assert len(comments) == 1
    assert comments[0]['reviewer_name'] == "Dr. Smith"
    assert comments[0]['comment_text'] == "This needs clarification about the units"
    assert comments[0]['comment_type'] == "question"


def test_multiple_comments(temp_db):
    """Test adding multiple comments."""
    comments_mgr = CommentsManager(temp_db)

    # Add review item
    temp_db.execute_update("""
        INSERT INTO ReviewQueue (job_id, source_agent, source_data, generated_content)
        VALUES (?, ?, ?, ?)
    """, ("job-123", "TestAgent", "{}", "test content"))

    item_id = 1

    # Add multiple comments
    comments_mgr.add_comment(item_id, "Dr. Smith", "First comment", "general")
    comments_mgr.add_comment(item_id, "Dr. Jones", "Second comment", "suggestion")
    comments_mgr.add_comment(item_id, "Dr. Brown", "Third comment", "concern")

    # Check count
    count = comments_mgr.get_comment_count(item_id)
    assert count == 3

    # Check retrieval
    comments = comments_mgr.get_comments(item_id)
    assert len(comments) == 3
    assert comments[0]['reviewer_name'] == "Dr. Smith"
    assert comments[1]['reviewer_name'] == "Dr. Jones"
    assert comments[2]['reviewer_name'] == "Dr. Brown"


# ============================================================================
# TEST FEATURE 2: QUALITY SCORE DISPLAY
# ============================================================================

def test_quality_score_calculator():
    """Test quality score calculation."""
    calculator = QualityScoreCalculator()

    good_content = """## Variable: patient_age

**Description:** Patient age at enrollment

**Data Type:** Integer

**Values:** 0-120 years

**Ontology Mappings:**
- OMOP Concept: 4265453 (Age)
- LOINC: 21611-9 (Age at enrollment)

Example: 45 years old
"""

    metrics = calculator.calculate_score(good_content)

    assert isinstance(metrics, QualityMetrics)
    assert 0 <= metrics.overall_score <= 100
    assert 0 <= metrics.completeness_score <= 100
    assert 0 <= metrics.ontology_mapping_score <= 100
    assert 0 <= metrics.clarity_score <= 100
    assert metrics.overall_score > 50  # Should be reasonably good


def test_quality_score_poor_content():
    """Test quality score with poor content."""
    calculator = QualityScoreCalculator()

    poor_content = "age"  # Minimal content

    metrics = calculator.calculate_score(poor_content)

    assert metrics.overall_score < 50  # Should be poor
    assert len(metrics.issues) > 0  # Should have issues
    assert metrics.completeness_score < 50


def test_quality_score_with_ontologies():
    """Test quality score with multiple ontologies."""
    calculator = QualityScoreCalculator()

    content_with_ontologies = """## Variable: lab_glucose

**Description:** Fasting blood glucose

**Data Type:** Float

**Ontology Mappings:**
- LOINC: 1558-6 (Glucose)
- OMOP Concept: 3004410 (Glucose measurement)
- SNOMED CT: 33747003 (Glucose)
"""

    metrics = calculator.calculate_score(content_with_ontologies)

    # Should score high on ontology mapping
    assert metrics.ontology_mapping_score >= 70


def test_quality_score_suggestions():
    """Test that suggestions are provided."""
    calculator = QualityScoreCalculator()

    content = """## Variable: test_var

**Description:** A test variable

**Data Type:** Integer
"""

    metrics = calculator.calculate_score(content)

    # Should have some suggestions
    assert len(metrics.suggestions) > 0


# ============================================================================
# TEST FEATURE 3: EXCEL EXPORT
# ============================================================================

def test_excel_exporter_initialization(temp_db):
    """Test ExcelExporter initialization."""
    exporter = ExcelExporter(temp_db)
    assert exporter.db == temp_db


def test_excel_export_basic(temp_db, sample_documentation):
    """Test basic Excel export."""
    exporter = ExcelExporter(temp_db)

    # Add approved items
    source_data = json.dumps({
        'variable_name': 'blood_pressure_sys',
        'data_type': 'integer'
    })

    temp_db.execute_update("""
        INSERT INTO ReviewQueue
        (job_id, source_agent, source_data, generated_content, approved_content, status)
        VALUES (?, ?, ?, ?, ?, ?)
    """, ("job-123", "PlainLanguageAgent", source_data, sample_documentation,
          sample_documentation, "Approved"))

    # Export
    output_path = "test_export.xlsx"
    result_path = exporter.export_job_to_excel("job-123", output_path)

    assert os.path.exists(result_path)
    assert result_path == output_path

    # Read and verify
    df_dict = pd.read_excel(result_path, sheet_name='Data Dictionary')
    assert len(df_dict) == 1
    assert 'blood_pressure_sys' in df_dict['Variable Name'].values

    # Cleanup
    if os.path.exists(output_path):
        os.remove(output_path)


def test_excel_export_multiple_variables(temp_db):
    """Test Excel export with multiple variables."""
    exporter = ExcelExporter(temp_db)

    # Add multiple approved items
    variables = ['age', 'sex', 'race']
    for var in variables:
        source_data = json.dumps({'variable_name': var, 'data_type': 'text'})
        content = f"## Variable: {var}\n\n**Description:** Test variable {var}"

        temp_db.execute_update("""
            INSERT INTO ReviewQueue
            (job_id, source_agent, source_data, generated_content, status)
            VALUES (?, ?, ?, ?, ?)
        """, ("job-123", "TestAgent", source_data, content, "Approved"))

    # Export
    output_path = "test_multi_export.xlsx"
    result_path = exporter.export_job_to_excel("job-123", output_path)

    # Verify
    df_dict = pd.read_excel(result_path, sheet_name='Data Dictionary')
    assert len(df_dict) == 3

    # Cleanup
    if os.path.exists(output_path):
        os.remove(output_path)


def test_excel_export_no_approved_items(temp_db):
    """Test Excel export with no approved items."""
    exporter = ExcelExporter(temp_db)

    # Try to export job with no approved items
    with pytest.raises(ValueError, match="No approved items found"):
        exporter.export_job_to_excel("nonexistent-job")


def test_extract_ontologies(temp_db, sample_documentation):
    """Test ontology extraction."""
    exporter = ExcelExporter(temp_db)

    ontologies = exporter._extract_ontologies(sample_documentation, {})

    assert len(ontologies) > 0

    # Check for LOINC
    loinc_found = any(ont['system'] == 'LOINC' for ont in ontologies)
    assert loinc_found

    # Check for OMOP
    omop_found = any(ont['system'] == 'OMOP' for ont in ontologies)
    assert omop_found


# ============================================================================
# TEST FEATURE 5: TEMPLATE LIBRARY
# ============================================================================

def test_template_library_initialization(temp_db):
    """Test TemplateLibrary initialization."""
    library = TemplateLibrary(temp_db)

    # Check table was created
    query = "SELECT name FROM sqlite_master WHERE type='table' AND name='FieldTemplates'"
    result = temp_db.execute_query(query)

    assert len(result) == 1
    assert result[0]['name'] == 'FieldTemplates'


def test_template_library_default_templates(temp_db):
    """Test that default templates are loaded."""
    library = TemplateLibrary(temp_db)

    templates = library.list_templates()

    assert len(templates) > 0

    # Check for demographics templates
    demo_templates = [t for t in templates if t['category'] == 'Demographics']
    assert len(demo_templates) > 0

    # Check for specific templates
    template_names = [t['template_name'] for t in templates]
    assert 'demographics_age' in template_names
    assert 'demographics_sex' in template_names


def test_find_matching_template(temp_db):
    """Test finding matching template."""
    library = TemplateLibrary(temp_db)

    # Test age matching
    age_template = library.find_matching_template('patient_age')
    assert age_template is not None
    assert age_template['template_name'] == 'demographics_age'

    # Test sex/gender matching
    sex_template = library.find_matching_template('gender')
    assert sex_template is not None
    assert sex_template['template_name'] == 'demographics_sex'

    # Test blood pressure matching
    bp_template = library.find_matching_template('bp_systolic')
    assert bp_template is not None
    assert bp_template['template_name'] == 'vitals_blood_pressure'


def test_apply_template(temp_db):
    """Test applying template."""
    library = TemplateLibrary(temp_db)

    # Apply age template
    doc = library.apply_template('patient_age', 'demographics_age')

    assert doc is not None
    assert 'patient_age' in doc
    assert 'OMOP' in doc
    assert 'Description' in doc


def test_apply_template_auto_match(temp_db):
    """Test applying template with auto-matching."""
    library = TemplateLibrary(temp_db)

    # Auto-match based on variable name
    doc = library.apply_template('subject_age')  # Should match age template

    assert doc is not None
    assert 'subject_age' in doc


def test_list_templates_by_category(temp_db):
    """Test listing templates by category."""
    library = TemplateLibrary(temp_db)

    # Get demographics templates
    demo_templates = library.list_templates(category='Demographics')

    assert len(demo_templates) > 0
    assert all(t['category'] == 'Demographics' for t in demo_templates)


def test_template_format_variable_name(temp_db):
    """Test that variable name is properly formatted in template."""
    library = TemplateLibrary(temp_db)

    doc = library.apply_template('my_custom_age_var', 'demographics_age')

    # Variable name should be in the output
    assert 'my_custom_age_var' in doc
    # But template text should also be there
    assert 'Patient age' in doc or 'age' in doc.lower()


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

def test_quality_score_and_export_integration(temp_db, sample_documentation):
    """Test integration of quality scoring and Excel export."""
    calculator = QualityScoreCalculator()
    exporter = ExcelExporter(temp_db)

    # Calculate score
    metrics = calculator.calculate_score(sample_documentation)
    assert metrics.overall_score > 0

    # Add to database
    source_data = json.dumps({
        'variable_name': 'blood_pressure_sys',
        'data_type': 'integer',
        'quality_score': metrics.overall_score
    })

    temp_db.execute_update("""
        INSERT INTO ReviewQueue
        (job_id, source_agent, source_data, generated_content, status)
        VALUES (?, ?, ?, ?, ?)
    """, ("job-123", "TestAgent", source_data, sample_documentation, "Approved"))

    # Export
    output_path = "test_integration.xlsx"
    result_path = exporter.export_job_to_excel("job-123", output_path)

    assert os.path.exists(result_path)

    # Cleanup
    if os.path.exists(output_path):
        os.remove(output_path)


def test_template_and_quality_integration(temp_db):
    """Test integration of template application and quality scoring."""
    library = TemplateLibrary(temp_db)
    calculator = QualityScoreCalculator()

    # Apply template
    doc = library.apply_template('patient_age', 'demographics_age')

    # Score the generated documentation
    metrics = calculator.calculate_score(doc)

    # Template-generated docs should score well
    assert metrics.overall_score > 60
    assert metrics.completeness_score > 60
    assert metrics.ontology_mapping_score > 60


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
