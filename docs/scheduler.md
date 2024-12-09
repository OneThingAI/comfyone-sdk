# Backend Scheduler

The ComfyOne SDK includes a backend scheduler that helps manage multiple ComfyUI instances.

## Overview

Each backend instance is uniquely associated with a single app_id, which represents a specific service type. This one-to-one relationship ensures dedicated resources and clear service boundaries.

For example:
- A backend with app_id "txt2img" can only handle text-to-image requests
- A backend with app_id "img2img" can only handle image-to-image requests
- A backend with app_id "upscale" can only handle upscaling requests

## API Response Structure

All API endpoints return a standardized response structure:

```json
{
    "code": 0,
    "msg": "success",
    "data": {...}
}
```
Example successful response:
```json
{
    "code": 0,
    "msg": "Backend added successfully",
    "data": {
        "backend": {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "instance_id": "instance_123",
            "app_id": "txt2img",
            "weight": 1,
            "state": "active"
        },
        "policy": {
            "policy_type": "round_robin",
            "limit": 1
        }
    }
}
```        
Example error response:
```json
{
    "code": 1,
    "msg": "Backend with this instance_id already exists",
    "data": null
}
```

The response structure is defined using Pydantic models for type safety and validation:
```python
from typing import Optional, TypeVar, Generic
from pydantic import BaseModel
T = TypeVar('T')
class APIResponse(BaseModel, Generic[T]):
    code: int = 0 # 0 for success, 1 for failure
    msg: str = "success"
    data: Optional[T] = None
```

Common response codes:
- `0`: Success - Operation completed successfully
- `1`: Error - Operation failed with error message in `msg` field

more details see [APIResponse](../comfyone/scheduler/models.py) and [API](../comfyone/scheduler/api.py)


## Backend Selection Policies

The scheduler supports different policies for backend selection:

1. Round Robin (limit: 1)
   - Selects one backend at a time in rotation
   - Useful for even load distribution

2. Weighted (limit: 1)
   - Selects up to 1 backend based on weight
   - Higher weight means higher priority
   - Good for prioritized load balancing

3. All Active (limit: 3)
   - Returns up to 3 active backends
   - Default policy if none specified

4. Random (limit: 1)
   - Randomly selects 1 backend from active backends
   - Good for simple load distribution without state
   - Useful when backend performance is similar

## Getting Started

### Starting the Scheduler

Run with uvicorn: 

```bash
uvicorn comfyone.scheduler.main:app --host 0.0.0.0 --port 8000
```

Or use the following code:

```python
from fastapi import FastAPI
from comfyone.scheduler.api import router

app = FastAPI()
app.include_router(router)
```

### API Endpoints

#### Managing Backends

List all backends in system:

```bash
curl "http://localhost:8000/v1/backends/all"
```

List all backends for specific app_id:

```bash
curl "http://localhost:8000/v1/{app_id}/backends/all"
```

get a specific app backend with policy specified by yourself:

```bash
curl "http://localhost:8000/v1/{app_id}/backends"
```


Add a backend:

```bash
curl -X POST "http://localhost:8000/v1/{app_id}/backends" \
  -H "Content-Type: application/json" \
  -d '{"app_id": "{app_id}", "instance_id": "{backend_id}", "weight": {weight}, "state": "active"}'
```

Remove a backend:

```bash
curl -X DELETE "http://localhost:8000/v1/{app_id}/backends/{backend_id}"
```

#### Backend State Management

Set backend to inactive:

```bash
curl -X PATCH "http://localhost:8000/v1/{app_id}/backends/{backend_id}?state=down"
```

Set backend to active:

```bash
curl -X PATCH "http://localhost:8000/v1/{app_id}/backends/{backend_id}?state=active"
```

State values:
- `active`: Backend is available for processing requests
- `down`: Backend is temporarily unavailable

#### Backend Configuration

Update backend's app_id:

```bash
curl -X PATCH "http://localhost:8000/v1/{current_app_id}/backends/{backend_id}/app?new_app_id={new_app_id}"
```

Update backend weight:

```bash
curl -X PATCH "http://localhost:8000/v1/{app_id}/backends/{backend_id}/weight?new_weight={weight}"
```

Weight requirements:
- Must be greater than or equal to 1 (integer)
- Used for weighted load balancing policy
- Higher weight means higher priority

#### Policy Management

List all supported policies:

```bash
curl "http://localhost:8000/v1/policies"
```

Update policy of a specific app:

```bash
curl -X PATCH "http://localhost:8000/v1/{app_id}/policy" \
  -H "Content-Type: application/json" \
  -d '{"policy_type": "{policy_type}", "limit": {limit}}'
```

## Backend Configuration

Each backend instance is configured with:
- Unique ID (auto-generated)
- Name
- Instance ID (instance_id in OnethingAI platform)
- Weight (for load balancing)
- State (active/inactive)

The scheduler uses SQLite to persistently store backend configurations at `./backends.db`.


