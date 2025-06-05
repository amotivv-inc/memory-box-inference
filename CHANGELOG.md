# Changelog

All notable changes to the OpenAI Inference Proxy will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial release of OpenAI Inference Proxy
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

### Security
- Fernet encryption for API keys at rest
- JWT token validation with configurable expiration
- Organization-level isolation
- User-scoped access control

## [1.0.0] - TBD

### Added
- First stable release
- Production-ready deployment configuration
- Comprehensive documentation suite
- Full test coverage

### Changed
- TBD based on community feedback

### Deprecated
- None

### Removed
- None

### Fixed
- None

### Security
- All API keys encrypted at rest
- JWT-based authentication
- Organization isolation enforced

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
