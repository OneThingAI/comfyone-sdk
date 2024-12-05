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

Each backend instance is uniquely associated with a single app_id, which represents a specific service type. This one-to-one relationship ensures dedicated resources and clear service boundaries. You can use the `update_backend_app_id` API to reassign a backend to a different app if needed.

For example:
- A backend with app_id "txt2img" can only handle text-to-image requests
- A backend with app_id "img2img" can only handle image-to-image requests
- A backend with app_id "upscale" can only handle upscaling requests

And the scheduler will automatically manage the load balancing, you can add failover by yourself use the `update_backend_status` API, if the backend is down, the scheduler will automatically remove it from the load balancing pool.

### Backend Selection Policies

The scheduler supports different policies for backend selection:

1. Round Robin (limit: 1)
   - Selects one backend at a time in rotation
   - Useful for even load distribution

2. Weighted (limit: 3)
   - Selects up to 3 backends based on weight
   - Higher weight means higher priority
   - Good for prioritized load balancing

3. All Active (limit: 5)
   - Returns up to 5 active backends
   - Default policy if none specified

4. Random (limit: 2)
   - Randomly selects 2 backend from active backends
   - Good for simple load distribution without state
   - Useful when backend performance is similar

TODO:
- Add more policies for load balancing

Here's how to use it:

### Starting the Scheduler

Run with uvicorn:
```bash
uvicorn comfyone.scheduler.main:app --host 0.0.0.0 --port 8000 --reload
```
The server will start on http://localhost:8000 with:
- Auto-reload enabled for development
- SQLite database at `./backends.db`
- API endpoints available at `/v1/{app_id}/backends`
- The database file will be created automatically in the current directory

Or use the following code to start the scheduler:

```python
from fastapi import FastAPI
from comfyone.scheduler.backend_scheduler import router
app = FastAPI()
app.include_router(router)
```

### Managing Backends
List all backends:
```bash
curl "http://localhost:8000/v1/{app_id}/backends"
```

Add a backend:
```bash
curl -X POST "http://localhost:8000/v1/{app_id}/backends" -H "Content-Type: application/json" -d '{"name": "backend1", "host": "{backend_id}"}'
```

Remove a backend:
```bash
curl -X DELETE "http://localhost:8000/v1/{app_id}/backends/{backend_id}"
```

Set backend to inactive:
```bash
curl -X PATCH "http://localhost:8000/v1/{app_id}/backends/{backend_id}?status=down"
```

Set backend to active:
```bash
curl -X PATCH "http://localhost:8000/v1/{app_id}/backends/{backend_id}?status=active"
```

The status can be:
- `active`: Backend is available for processing requests
- `down`: Backend is temporarily unavailable

### Update backend's app_id
```bash
curl -X PATCH "http://localhost:8000/v1/{current_app_id}/backends/{backend_id}/app?new_app_id={new_app_id}"
```

Update backend weight:

```bash
curl -X PATCH "http://localhost:8000/v1/{app_id}/backends/{backend_id}/weight" -H "Content-Type: application/json" -d '{"weight": {weight}}'
```
The weight must be:
- Greater than 0
- Used for weighted load balancing policy
- Higher weight means higher priority in load balancing

### Backend Configuration

Each backend instance is configured with:
- Unique ID (auto-generated)
- Name
- Host
- Weight (for load balancing)
- Status (active/inactive)

The scheduler uses SQLite to persistently store backend configurations.


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


