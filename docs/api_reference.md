# ComfyOne SDK API Reference

## Table of Contents
- [Installation](#installation)
- [Basic Usage](#basic-usage)
- [Core Classes](#core-classes)
  - [ComfyOne](#comfyone)
  - [ComfyOneClient](#comfyoneclient)
  - [WebSocket Support](#websocket-support)
- [Error Handling](#error-handling)
- [Models](#models)
- [Examples](#examples)

## Installation 

```bash
pip install git+https://github.com/OneThingAI/comfyone-sdk.git
```

## Basic Usage

```python
from comfyone import ComfyOne

# Initialize the client
client = ComfyOne(
    api_key="your_api_key",
    debug=True  # Enable debug mode for verbose logging
)
```

## Core Classes

### ComfyOne

Main client class that provides access to all API functionality.

#### Parameters
- `api_key` (str): Your OneThingAI API key
- `domain` (str, optional): API domain. Default: "pandora-server-cf.onethingai.com"
- `max_retries` (int, optional): Maximum number of retry attempts. Default: 3
- `timeout` (int, optional): Request timeout in seconds. Default: 5
- `debug` (bool, optional): Enable debug mode. Default: False
- `log_file` (Path, optional): Custom log file path. Default: None

### ComfyOneClient

The API client class that handles all HTTP requests to the ComfyOne API.

#### Backend Management Methods

1. **get_available_backends()**
   - Gets a list of all available backend instances
   - Returns: `APIResponse`

2. **register_backend(instance_id: str)**
   - Registers a new backend instance
   - Parameters:
     - `instance_id` (str): Unique identifier for the instance
   - Returns: `APIResponse`

3. **delete_backend(instance_id: str)**
   - Deletes a specific backend instance
   - Parameters:
     - `instance_id` (str): ID of the instance to delete
   - Returns: `APIResponse`

4. **set_backend_state(name: str, state: str)**
   - Sets the state of a backend instance
   - Parameters:
     - `name` (str): Instance name
     - `state` (str): New state ('up' or 'down')
   - Returns: `APIResponse`

#### Workflow Management Methods

1. **create_workflow(payload: WorkflowPayload)**
   - Creates a new workflow
   - Parameters:
     - `payload`: WorkflowPayload object containing workflow configuration
   - Returns: `APIResponse`

2. **get_workflows()**
   - Gets all available workflows
   - Returns: `APIResponse`

3. **get_workflow(workflow_id: str)**
   - Gets details of a specific workflow
   - Parameters:
     - `workflow_id` (str): ID of the workflow
   - Returns: `APIResponse`

4. **update_workflow(workflow_id: str, payload: WorkflowPayload)**
   - Updates an existing workflow
   - Parameters:
     - `workflow_id` (str): ID of the workflow to update
     - `payload`: Updated workflow configuration
   - Returns: `APIResponse`

#### Prompt and File Management

1. **prompt(payload: PromptPayload)**
   - Sends a prompt request to generate images
   - Parameters:
     - `payload`: Prompt configuration
   - Returns: `APIResponse`

2. **upload_file(file_path: str)**
   - Uploads a file to ComfyOne
   - Parameters:
     - `file_path` (str): Path to the file
   - Returns: `APIResponse`

### WebSocket Support

The SDK includes WebSocket support for real-time task monitoring:

```python
def handle_progress(data):
    print(f"Task {data['taskId']} progress: {data['data']['process']}%")

# Initialize WebSocket client
ws_client = client.ws
ws_client.add_message_handler("progress", handle_progress)
ws_client.start()
```

## Error Handling

The SDK provides specific exception classes for different types of errors:

```python
class ComfyOneError(Exception):
    """Base exception for ComfyOne SDK"""
    pass

class ValidationError(ComfyOneError):
    """Validation related errors"""
    pass

class APIError(ComfyOneError):
    """API related errors"""
    pass

class AuthenticationError(APIError):
    """Authentication related errors"""
    pass

class ConnectionError(APIError):
    """Connection related errors"""
    pass
```

## Models

The SDK uses Pydantic models for request/response validation:

```python
class IOType(str, Enum):
    IMAGE = "image"
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"

class WorkflowInput(BaseModel):
    id: str
    type: IOType
    name: str

class WorkflowInputPayload(BaseModel):
    inputs: List[WorkflowInput]

class WorkflowOutput(BaseModel):
    id: str

class WorkflowOutputPayload(BaseModel):
    outputs: List[WorkflowOutput]

class WorkflowPayload(BaseModel):
    name: str
    inputs: WorkflowInputPayload
    outputs: WorkflowOutputPayload
    workflow: Dict[str, Any]
```

## Examples

Here's a complete example demonstrating workflow creation and image generation:

```python
def main():
    # Initialize API client
    client = ComfyOne(api_key="your_api_key", debug=True)

    # Register backend instances
    instance_ids = ["instance_1", "instance_2"]
    for instance_id in instance_ids:
        client.api.register_backend(instance_id)
    
    # Initialize WebSocket client
    ws_client = client.ws
    
    # Define workflow configuration
    workflow_payload = WorkflowPayload(
        name="test",
        inputs=WorkflowInputPayload(
            inputs=[
                WorkflowInput(id='5', type=IOType.NUMBER, name='height'),
                WorkflowInput(id='5', type=IOType.NUMBER, name='width')
            ]
        ),
        outputs=WorkflowOutputPayload(
            outputs=[WorkflowOutput(id='9')]
        ),
        workflow=workflow_data  # Your workflow configuration
    )

    # Create workflow and generate image
    workflow_result = client.api.create_workflow(workflow_payload)
    if workflow_result.code == 0:
        prompt_payload = PromptPayload(
            workflow_id=workflow_result.data['id'],
            inputs=[
                PromptInput(id="5", params={"width": 1024, "height": 1024})
            ]
        )
        prompt_result = client.api.prompt(prompt_payload)
```

For more detailed examples and use cases, please refer to the examples directory in the SDK repository.