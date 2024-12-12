# ComfyOne SDK

ComfyOne SDK is a Python library that provides a convenient way to interact with the ComfyOne API for OneThingAI's comfyui workflow management.

API documentation: [ComfyOne API](https://onethingai.yuque.com/org-wiki-onethingai-gexhu2/help/asf9hbbuf0qgrpg8)

## Installation

You can install the package using pip: 

```bash
pip install git+https://github.com/OneThingAI/comfyone-sdk.git
```
Or install from source:

```bash
git clone https://github.com/OneThingAI/comfyone-sdk
cd comfyone-sdk
pip install -e .
```

## Requirements

- Python >= 3.7
- requests >= 2.25.0
- websocket-client >= 1.0.0
- pydantic >= 1.10.0
- sqlalchemy >= 2.0.0
- fastapi >= 0.100.0

## Quick Start

See [`examples/main.py`](examples/main.py) for a quick start example that demonstrates how to use the SDK to generate images and manage workflows.

## Features

- Easy-to-use Python interface for ComfyOne API
- WebSocket support for real-time task monitoring
- Comprehensive workflow management
- Backend scheduler for managing ComfyUI instances
- Type hints and validation using Pydantic
- Error handling and retry mechanisms
- Debug mode for development

## API Documentation

See [API Reference](docs/api_reference.md) for detailed API documentation.

## Backend Scheduler

The SDK includes a backend scheduler that helps manage multiple ComfyUI instances. 

For detailed information about the scheduler, including:
- Backend selection policies
- API endpoints
- Configuration options
- Usage examples

Quick Start:
python -m comfyone.scheduler.launch_server

Start a example backend scheduler:

```bash
cd comfyone/examples
python backend_scheduler.py
```
or start it by python module:
```bash
python -m comfyone.examples.backend_scheduler

See [Scheduler Documentation](docs/scheduler.md)

## Development

To contribute to the project:

1. Fork the repository
2. Create a new branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please open an issue in the GitHub repository or contact the maintainers.


