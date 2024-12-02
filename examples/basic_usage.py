import sys
import signal
import json
from dataclasses import asdict
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

def main():
    """
    ComfyOne SDK基础使用示例
    演示了如何：
    1. 初始化SDK客户端
    2. 建立WebSocket连接
    3. 创建工作流
    4. 发送生成请求
    """
    # 初始化SDK客户端
    # 注意：请将 your-api-key 替换为您的实际API密钥
    # 注意：请将 domain 替换为您的实际域名
    # debug=True 会打印更多的调试信息, 默认是关闭的，调试完成后请关闭
    client = ComfyOne(
        api_key="97ad8bccd51ab247f7535d9c788ef949",
        debug=True
    )
    
    try:
        # 创建工作流配置
        # 这里定义了工作流的输入参数，包括图像的高度和宽度
        workflow_inputs = WorkflowInputPayload(
            inputs=[
                WorkflowInput(id='5', type=IOType.NUMBER, name='height'),  # 高度输入节点
                WorkflowInput(id='5', type=IOType.NUMBER, name='width')    # 宽度输入节点
            ]
        )

        workflow_outputs = WorkflowOutputPayload(
            outputs=[WorkflowOutput(id='9')]
        )
        
        # 从JSON文件加载工作流定义
        # 注意：确保test_flow.json文件存在且格式正确
        with open("test_flow.json", 'r', encoding='utf-8-sig') as f:
            workflow_data = json.load(f)
        
        # 构造工作流创建请求
        workflow_payload = WorkflowPayload(
            name = "test",              # 工作流名称
            inputs = workflow_inputs,   # 输入参数配置
            outputs = workflow_outputs, # 输出节点ID列表
            workflow = workflow_data    # 工作流定义数据
        )

        # 发送创建工作流请求
        create_workflow_result = client.api.create_workflow(workflow_payload)
        # 如果工作流创建成功，继续发送生成请求
        if create_workflow_result.code == 0:
            # 设置生成参数
            prompt_params = {"width": 1024, "height": 1024} # 根据Create Workflow时填写的inputs填写
            
            # 构造输入参数
            prompt_input = PromptInput(
                id="5",              # 输入节点ID
                params=prompt_params # 参数配置
            )
            
            # 构造生成请求
            prompt_payload = PromptPayload(
                workflow_id=create_workflow_result.data['id'],  # 工作流ID
                inputs=[{"id": "5", "params": {"width": 1024, "height": 1024}}]                          # 输入参数列表
            )
            
            # 发送生成请求
            prompt_result = client.api.prompt(prompt_payload)
            print(prompt_result)
    except KeyboardInterrupt:
        # 处理Ctrl+C中断
        print("\n正在关闭连接...")
    except Exception as e:
        # 处理其他异常
        print(f"发生错误: {e}")
    finally:
        # 确保正确关闭所有连接
        client.close()

if __name__ == "__main__":
    main() 