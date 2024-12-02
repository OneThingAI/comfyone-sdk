import sys
import signal
import json
import time
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
    # Replace with your actual credentials
    API_KEY = "97ad8bccd51ab247f7535d9c788ef949"
    INSTANCE_ID = "dptoveqgg66ywpv8-n11h8g6z"

    # Initialize API client
    client = ComfyOne(API_KEY, instance_id=INSTANCE_ID, debug=True)

    # 查询可用后端
    backends = client.api.get_available_backends()
    print(backends)

    # 如果实例没有注册到ComfyOne，则注册
    is_registered = False
    for backend in backends.data:
        if backend["name"] == INSTANCE_ID:
            is_registered = True
            break
    if not is_registered:
        register_result = client.api.register_backend(INSTANCE_ID)
        if register_result is not None and register_result.code == 0:
            print(f"注册实例成功: {register_result.data}")
        else:
            print(f"注册实例失败: {register_result.code}, {register_result.msg}")
            exit(1)
    
    # Initialize WebSocket client
    ws_client = OneThingAIWebSocket(API_KEY)
    
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
            print(f"任务 {data['taskId']} 已完成")
            # Here you can add code to fetch the output content through the API
            
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