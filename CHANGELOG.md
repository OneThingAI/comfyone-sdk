# Changelog

All notable changes to ComfyOne SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
## [0.1.3] - 2024-12-12

### Added
- Simple launcher for backend scheduler

## [0.1.2] - 2024-12-05

### Added
- Backend scheduler for managing multiple ComfyUI instances
- SQLite database for persistent backend storage
- Multiple backend selection policies:
  - Round Robin (with limit=1)
  - Weighted (with limit=3)
  - All Active (with limit=5)
  - Random (with limit=2)
- Backend management APIs:
  - Add/remove backends
  - Update backend status (active/down)
  - Update backend weight
  - Update backend app_id
- FastAPI integration for scheduler service

### Changed
- Updated dependencies to include SQLAlchemy and FastAPI
- Enhanced documentation with scheduler usage examples
- Improved error handling in backend management

## [0.1.1] - 2024-12-02

### Added
- WebSocket support for real-time task monitoring
- Debug context manager for better debugging experience
- Comprehensive logging system
- Type validation using Pydantic models

### Changed
- Improved error handling with specific exception classes
- Enhanced retry mechanism for API requests

### Fixed
- Type hints in API response models
- WebSocket connection stability issues


[0.1.2]: https://github.com/OneThingAI/comfyone-sdk/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/OneThingAI/comfyone-sdk/compare/v0.1.0...v0.1.1