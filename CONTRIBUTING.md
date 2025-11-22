# Contributing to ADE Healthcare Documentation

Thank you for your interest in contributing to the Agent Development Environment (ADE) for Healthcare Data Documentation! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Environment Setup](#development-environment-setup)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
- [Testing Guidelines](#testing-guidelines)
- [Code Style and Standards](#code-style-and-standards)
- [Documentation Guidelines](#documentation-guidelines)
- [Submitting Changes](#submitting-changes)
- [Reporting Issues](#reporting-issues)

## Code of Conduct

This project adheres to a code of conduct that we expect all contributors to follow:

- Be respectful and inclusive
- Welcome newcomers and help them get started
- Focus on constructive feedback
- Assume good intentions
- Respect differing viewpoints and experiences

## Getting Started

1. **Fork the Repository**
   ```bash
   # Fork on GitHub, then clone your fork
   git clone https://github.com/YOUR_USERNAME/rdd_orch.git
   cd rdd_orch
   ```

2. **Add Upstream Remote**
   ```bash
   git remote add upstream https://github.com/dspacks/rdd_orch.git
   ```

3. **Create a Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Environment Setup

### Prerequisites

- Python 3.8 or higher
- Google Gemini API key
- Git
- Jupyter Notebook (for notebook development)

### Installation

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Install Development Dependencies**
   ```bash
   pip install pytest pytest-cov black flake8 mypy
   ```

3. **Set Up API Key**
   ```bash
   export GOOGLE_API_KEY="your-api-key-here"
   ```

4. **Verify Installation**
   ```bash
   python -m pytest tests/
   ```

## Project Structure

```
rdd_orch/
├── ade_healthcare_documentation.ipynb  # Main implementation
├── agentic_enhancements.py            # HITL enhancements
├── hitl_fixes.py                      # Core fixes
├── hitl_fixes_integration.py          # UI integration
├── diagnostic_gemini_api.py           # Diagnostics
├── docs/                              # Documentation
├── tests/                             # Test suite
├── examples/                          # Example notebooks
├── healthcare_agent_deploy/          # Deployment config
└── archived_versions/                # Archived files
```

## Development Workflow

### 1. Keep Your Fork Updated

```bash
git fetch upstream
git checkout main
git merge upstream/main
```

### 2. Make Your Changes

- Write clean, readable code
- Follow existing code style and patterns
- Add tests for new functionality
- Update documentation as needed

### 3. Test Your Changes

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_hitl_fixes.py

# Run with coverage
pytest --cov=. tests/
```

### 4. Commit Your Changes

```bash
git add .
git commit -m "Brief description of changes

Detailed explanation of what was changed and why.
Fixes #issue_number (if applicable)"
```

## Testing Guidelines

### Writing Tests

- Place tests in the `tests/` directory
- Name test files `test_*.py`
- Name test functions `test_*`
- Use descriptive test names that explain what is being tested

Example:
```python
import unittest
from hitl_fixes import EnhancedDatabaseManager

class TestEnhancedDatabaseManager(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        self.db = EnhancedDatabaseManager(":memory:")

    def test_transaction_rollback_on_error(self):
        """Test that transactions rollback properly on errors."""
        # Test implementation
        pass

    def tearDown(self):
        """Clean up after tests."""
        self.db.close()
```

### Running Tests

```bash
# All tests
pytest

# Specific test class
pytest tests/test_hitl_fixes.py::TestEnhancedDatabaseManager

# Specific test method
pytest tests/test_hitl_fixes.py::TestEnhancedDatabaseManager::test_transaction_rollback_on_error

# With verbose output
pytest -v

# With coverage report
pytest --cov=. --cov-report=html
```

### Test Coverage

- Aim for at least 80% code coverage for new features
- All bug fixes should include a regression test
- Critical paths should have 100% coverage

## Code Style and Standards

### Python Code Style

We follow PEP 8 with these specifics:

- **Line Length**: 100 characters maximum
- **Indentation**: 4 spaces (no tabs)
- **Naming Conventions**:
  - Classes: `PascalCase`
  - Functions/methods: `snake_case`
  - Constants: `UPPER_SNAKE_CASE`
  - Private methods: `_leading_underscore`

### Code Formatting

Format your code with Black before committing:

```bash
black *.py tests/*.py
```

### Linting

Check your code with flake8:

```bash
flake8 *.py tests/*.py --max-line-length=100
```

### Type Hints

Use type hints for function signatures:

```python
def process_data_dictionary(
    source_data: dict,
    source_file: str,
    auto_approve: bool = False
) -> str:
    """Process a data dictionary and return job ID.

    Args:
        source_data: Dictionary containing the data to process
        source_file: Name of the source file
        auto_approve: Whether to automatically approve all items

    Returns:
        Job ID string
    """
    pass
```

### Docstrings

Use Google-style docstrings:

```python
def example_function(param1: str, param2: int) -> bool:
    """Brief one-line description.

    Longer description providing more details about the function,
    its purpose, and any important implementation notes.

    Args:
        param1: Description of first parameter
        param2: Description of second parameter

    Returns:
        Description of return value

    Raises:
        ValueError: When param2 is negative

    Example:
        >>> example_function("test", 5)
        True
    """
    pass
```

## Documentation Guidelines

### When to Update Documentation

- Adding new features or agents
- Changing existing APIs or interfaces
- Fixing bugs that affect documented behavior
- Adding new configuration options

### Documentation Files

- **README.md**: Overview and quick start
- **docs/**: Detailed documentation
- **CHANGELOG.md**: Version history
- **Inline comments**: Complex logic only

### Documentation Style

- Use clear, concise language
- Provide code examples
- Include screenshots for UI features
- Keep examples up to date

## Submitting Changes

### Pull Request Process

1. **Update Documentation**
   - Update README.md if needed
   - Update relevant docs in `docs/`
   - Add entry to CHANGELOG.md

2. **Ensure Tests Pass**
   ```bash
   pytest tests/
   ```

3. **Push to Your Fork**
   ```bash
   git push origin feature/your-feature-name
   ```

4. **Create Pull Request**
   - Go to GitHub and create a pull request
   - Use a descriptive title
   - Fill out the PR template
   - Link related issues

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] All existing tests pass
- [ ] New tests added for new features
- [ ] Manual testing completed

## Checklist
- [ ] Code follows project style guidelines
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] No new warnings or errors
```

### Review Process

- Maintainers will review your PR
- Address any requested changes
- Once approved, maintainers will merge

## Reporting Issues

### Bug Reports

Include:
- **Description**: Clear description of the bug
- **Steps to Reproduce**: Detailed steps
- **Expected Behavior**: What should happen
- **Actual Behavior**: What actually happens
- **Environment**: Python version, OS, dependencies
- **Error Messages**: Full error messages and stack traces

### Feature Requests

Include:
- **Description**: What feature you'd like to see
- **Use Case**: Why this feature would be useful
- **Proposed Solution**: How you think it should work
- **Alternatives**: Other approaches you've considered

## Questions and Support

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Documentation**: Check `docs/` directory first

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Recognition

Contributors will be recognized in:
- GitHub contributors page
- CHANGELOG.md for significant contributions
- README.md acknowledgments section

Thank you for contributing to ADE Healthcare Documentation! 🎉
