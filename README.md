# ComfyOne SDK

ComfyOne SDK is a Python library that provides a convenient way to interact with the ComfyOne API for AI image generation and workflow management.

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

## Quick Start

See [`examples/main.py`](examples/main.py) for a quick start example that demonstrates how to use the SDK to generate images and manage workflows.

## Features

- Easy-to-use Python interface for ComfyOne API
- WebSocket support for real-time task monitoring
- Comprehensive workflow management
- Type hints and validation using Pydantic
- Error handling and retry mechanisms
- Debug mode for development

## API Documentation

### Main Classes

#### ComfyOne
The main client class that provides access to all API functionality.

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


