# Changelog

All notable changes to the Enterprise AI Governance Platform will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-06-12

### Added
- First stable release of Enterprise AI Governance Platform
- Production-ready deployment configuration
- Comprehensive documentation suite including User Guide
- Full test coverage

### Changed
- Updated license from Apache-2.0 to GNU Affero General Public License v3.0 (AGPL-3.0) for better intellectual property protection

### Security
- All API keys encrypted at rest
- JWT-based authentication
- Organization isolation enforced
- User-scoped access control

## [0.1.0] - 2025-05-15

### Added
- Initial beta release
- JWT-based authentication system
- Organization and user management
- API key encryption and secure storage
- User-scoped API key validation with priority-based resolution
- OpenAI Responses API proxy support (streaming and non-streaming)
- Real-time usage tracking and cost calculation
- Response rating system with feedback
- Session management for grouping related requests
- Comprehensive audit trail for all API interactions
- Docker and Docker Compose deployment configuration
- Quickstart script for easy setup
- Management scripts for organizations, users, and API keys
- Comprehensive test suite
- Python client example with full feature demonstration
- Detailed documentation (README, Admin Guide, Deployment Guide)
- CORS support for browser-based applications
- Health check endpoint with OpenAI connectivity verification
- Automatic user creation on first request
- Response ID storage for rating by OpenAI response ID
- Persona management system with user-scoped access control
- Persona analytics endpoint with detailed usage metrics
- Support for large personas (up to 40K tokens)

### Security
- Fernet encryption for API keys at rest
- JWT token validation with configurable expiration
- Organization-level isolation
- User-scoped access control

---

## Version History Format

### [Version] - YYYY-MM-DD

#### Added
- New features

#### Changed
- Changes in existing functionality

#### Deprecated
- Soon-to-be removed features

#### Removed
- Removed features

#### Fixed
- Bug fixes

#### Security
- Security updates and vulnerability fixes
