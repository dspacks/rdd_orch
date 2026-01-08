# Changelog

All notable changes to the ADE Healthcare Documentation project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.1.0] - 2025-11-22

### Added
- **Repository Organization**: Reorganized repository structure with dedicated `docs/`, `tests/`, and `archived_versions/` directories
- **Extended Agent System**:
  - ValidationAgent for quality and consistency checks
  - VersionControlAgent for tracking documentation history
  - DataConventionsAgent for naming pattern analysis
  - DesignImprovementAgent for documentation enhancement
  - HigherLevelDocumentationAgent for instrument-level docs
- **Batch Processing**: SnippetManager and BatchProcessor for handling multiple files
- **Enhanced HITL Workflow**:
  - Smart retry logic with exponential backoff
  - Progress persistence for resumable workflows
  - Enhanced dashboard with real-time updates
  - Rate limiting UI with progress widgets
- **Safety Improvements**:
  - Database transaction management
  - File size and content validation
  - Safe orchestration with error handling
  - Comprehensive test coverage for HITL fixes

### Changed
- Improved token efficiency with Toon notation (40-70% reduction)
- Enhanced database schema with better indexes and constraints
- Updated documentation structure for better navigation
- Modernized API integration with Gemini 2.0 Flash

### Fixed
- Job status constraint errors in HITL workflow
- Database locking issues with proper transaction handling
- File upload validation and error handling
- Context compaction triggering logic

### Documentation
- Added comprehensive CHANGELOG.md for version tracking
- Created CONTRIBUTING.md with contributor guidelines
- Added pyproject.toml for proper Python packaging
- Updated README.md with current repository structure
- Improved inline documentation across all modules

## [3.0.0] - 2024-11-15

### Added
- **Core Multi-Agent System**:
  - DataParserAgent for data conversion
  - TechnicalAnalyzerAgent for field analysis
  - DomainOntologyAgent for healthcare terminology mapping
  - PlainLanguageAgent for human-readable documentation
  - DocumentationAssemblerAgent for final compilation
- **Toon Notation System**: Custom encoding for token efficiency
- **Human-in-the-Loop (HITL) Workflow**: Review, approve, reject, clarify
- **SQLite Persistence**: Complete database schema for jobs, reviews, and context
- **Context Management**: Working vs long-term memory with compaction
- **Vertex AI Deployment**: Production-ready deployment configuration

### Documentation
- PROJECT_OVERVIEW.md with detailed showcase
- QUICK_REFERENCE.md with code examples
- AGENTS.md with complete agent documentation
- DATABASE_SCHEMA.md with ERD diagrams
- VERTEX_AI_DEPLOYMENT.md for production setup

## [2.0.0] - 2024-10-xx

### Added
- Initial multi-agent architecture
- Basic HITL workflow
- SQLite database integration
- Gemini API integration

## [1.0.0] - 2024-09-xx

### Added
- Initial proof of concept
- Single-agent documentation generation
- Basic data parsing capabilities

---

## Version History Summary

- **v3.1** - Extended agents, batch processing, enhanced safety, repository cleanup
- **v3.0** - Core multi-agent system with Toon notation and HITL workflow
- **v2.0** - Multi-agent architecture with database persistence
- **v1.0** - Initial proof of concept

## Upgrade Notes

### Upgrading to 3.1
- No breaking changes from 3.0
- Database schema is backward compatible
- New agents are optional and can be integrated incrementally
- Tests have been reorganized to `tests/` directory
- Documentation moved to `docs/` directory

### Upgrading to 3.0
- Major architectural change from single-agent to multi-agent
- Database migration required (see DATABASE_SCHEMA.md)
- API key configuration remains the same

## Future Releases

See [README.md](README.md#roadmap) for planned features and roadmap.
