import sys
import signal
import json
import time
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from comfyone import ComfyOne
from comfyone.api.models import (
    IOType,
    WorkflowInput, 
    WorkflowOutput,
    WorkflowInputPayload,
    WorkflowOutputPayload,
    PromptInput, 
    PromptPayload, 
    WorkflowPayload
)
from comfyone.api.websocket.websocket_client import OneThingAIWebSocket

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print("\nShutdown signal received. Closing connections...")
    if hasattr(signal_handler, 'ws_client'):
        signal_handler.ws_client.close()
    sys.exit(0)

def main():
    # Initialize API client
    # Replace with your actual credentials
    client = ComfyOne("your_api_key", 
                      debug=True)

    # Replace with your actual instance IDs need to register to ComfyOne
    instance_ids_to_register = set(["instance_1", "instance_2"])
    
    # Query available backends
    existing_backends = client.api.get_available_backends()
    print(existing_backends)

    # If the instance is not registered to ComfyOne, register it
    existing_instance_ids = set(backend['name'] for backend in existing_backends.data)
    need_register_instance_ids = instance_ids_to_register - existing_instance_ids
    for instance_id in need_register_instance_ids:
        register_result = client.api.register_backend(instance_id)
        if register_result is not None and register_result.code == 0:
            print(f"Register instance success: {register_result.data}")
        else:
            print(f"Register instance failed: {register_result.code}, {register_result.msg}")
            continue
    
    # Initialize WebSocket client
    ws_client = OneThingAIWebSocket(client.api.api_key)
    
    # Store ws_client in signal_handler for cleanup
    signal_handler.ws_client = ws_client
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Define workflow configuration
    workflow_inputs = WorkflowInputPayload(
            inputs=[
                WorkflowInput(id='5', type=IOType.NUMBER, name='height'),  # 高度输入节点
                WorkflowInput(id='5', type=IOType.NUMBER, name='width')    # 宽度输入节点
            ]
        )

    workflow_outputs = WorkflowOutputPayload(
        outputs=[
            WorkflowOutput(id='9', type='image')
        ]
    ) 
    
    with open("test_flow.json", 'r', encoding='utf-8-sig') as f:
        workflow_data = json.load(f)
    
    workflow_payload = WorkflowPayload(
        name="test",
        inputs=workflow_inputs,
        outputs=workflow_outputs,
        workflow=workflow_data
    )

    # Define WebSocket message handlers
    def handle_pending(data):
        print(f"任务 {data['taskId']} 等待执行, 当前位置: {data['data']['current']}")

    def handle_progress(data):
        print(f"任务 {data['taskId']} 正在执行, 进度: {data['data']['process']}%")

    def handle_finished(data):
        if data['data']['success']:
            status_response = client.api.get_prompt_status(data['taskId'])
            print(data, status_response)
            print(f"任务 {data['taskId']} 已完成")
            
            if 'images' in status_response.data:
                try:
                    # Download to current directory with automatic naming
                    for url in status_response.data["images"]:
                        saved_path = client.api.download_file(url)
                        print(f"结果已下载到: {saved_path}")
                except Exception as e:
                    print(f"下载文件失败: {str(e)}")

    def handle_error(data):
        print(f"任务执行出错: {data['data']['message']}")

    # Register message handlers
    ws_client.add_message_handler("pendding", handle_pending)
    ws_client.add_message_handler("progress", handle_progress)
    ws_client.add_message_handler("finished", handle_finished)
    ws_client.add_message_handler("error", handle_error)

    # Start WebSocket client
    ws_client.start()

    try:
        # Create workflow
        create_workflow_result = client.api.create_workflow(workflow_payload)

        # Generate image
        if create_workflow_result.code == 0:
            prompt_params = {"width": 1024, "height": 1024}
            
            prompt_input = PromptInput(
                id="5",              # 输入节点ID
                params=prompt_params # 参数配置
            )
            
            prompt_payload = PromptPayload(
                workflow_id=create_workflow_result.data['id'],
                inputs=[prompt_input]
            )
            
            prompt_result = client.api.prompt(prompt_payload)
            if prompt_result.code == 0:    
                print(f"prompt_result: {prompt_result}")
                print(prompt_result.data)
            else:
                print(f"生成图片失败: {prompt_result.code}, {prompt_result.msg}")
                sys.exit(1)
        else:
            print(f"创建工作流失败: {create_workflow_result.code}, {create_workflow_result.msg}")
            sys.exit(1)

        # Keep the main thread running
        while True:
            time.sleep(1)
            
    except Exception as e:
        print(f"Error: {e}")
        ws_client.close()
        sys.exit(1)

if __name__ == "__main__":
    main() 