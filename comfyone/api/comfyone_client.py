import requests
import json
import os
import time
import logging
from typing import Optional, List
from .models import APIResponse, WorkflowPayload, PromptPayload
from .exceptions import APIError, AuthenticationError, ConnectionError

class ComfyOneClient:
    """
    ComfyOne API客户端类
    用于处理与ComfyOne服务的所有API交互
    """
    def __init__(self, api_key: str, base_url: str = "https://pandora-server-cf.onethingai.com", 
                 max_retries: int = 3, timeout: int = 5, logger: Optional[logging.Logger] = None):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')  # Remove trailing slash if present
        self.max_retries = max_retries
        self.timeout = timeout
        self.logger = logger or logging.getLogger(__name__)
        self.headers = {
            "Authorization": f"Bearer {api_key}"
        }

    def _request_api(self, api: str, payload: dict = None, method: str = "GET") -> APIResponse:
        """向ComfyOne API发送请求的通用函数"""
        url = f"{self.base_url}/{api}"
        self.logger.debug(f"API Request: {method} {url}")
        try:
            retry_count = 0
            while retry_count < self.max_retries:
                try:
                    if method == "POST" and payload and "file" in payload:
                        response = requests.request(
                            method, 
                            url, 
                            headers=self.headers,
                            files=payload,
                            timeout=self.timeout
                        )
                    else:
                        response = requests.request(
                            method, 
                            url, 
                            headers=self.headers,
                            json=payload if payload else None,
                            timeout=self.timeout
                    )
                    
                    if response.status_code == 401:
                        self.logger.error("API Authentication failed")
                        raise AuthenticationError(401, "Invalid API key")
                    
                    response.raise_for_status()
                    response_data = response.json()
                    self.logger.debug(f"API Response: {response.status_code} - {api}")
                    return APIResponse(**response_data)
                    
                except requests.exceptions.Timeout:
                    retry_count += 1
                    if retry_count == self.max_retries:
                        self.logger.error(f"API timeout after {self.max_retries} retries: {api}")
                        raise ConnectionError("API request timed out")
                    self.logger.warning(f"API timeout, retry {retry_count}/{self.max_retries}: {api}")
                    time.sleep(2 ** retry_count)
                    
                except requests.exceptions.RequestException as e:
                    retry_count += 1
                    if retry_count == self.max_retries:
                        self.logger.error(f"API failed after {self.max_retries} retries: {api}")
                        raise ConnectionError(f"API request failed: {str(e)}")
                    self.logger.warning(f"API error, retry {retry_count}/{self.max_retries}: {str(e)}")
                    time.sleep(2 ** retry_count)
                    
        except Exception as e:
            self.logger.error(f"API Error ({api}): {str(e)}")
            if isinstance(e, (AuthenticationError, ConnectionError)):
                raise
            raise APIError(500, str(e))

    def get_available_backends(self) -> APIResponse:
        """
        查询所有可用的ComfyOne后端服务实例
        
        Returns:
            APIResponse: 包含可用后端列表的响应数据
        """
        return self._request_api("v1/backends")

    def register_backend(self, instance_id: str) -> APIResponse:
        """
        注册一个新的实例作为ComfyOne后端服务。
        该函数将提供的实例ID添加到ComfyOne后端管理系统中，
        使其能够处理图像生成请求和工作流处理。
        
        参数:
            instance_id (str): 要注册的实例的唯一标识符
            
        返回:
            APIResponse: API响应数据
        """
        payload = {"instance_id": instance_id}
        return self._request_api("v1/backends", payload, "POST")

    def delete_backend(self, instance_id: str) -> APIResponse:
        """
        删除指定的后端服务实例
        
        参数:
            instance_id (str): 要删除的实例ID
            
        返回:
            APIResponse: API响应数据
        """
        return self._request_api(f"v1/backends/{instance_id}", method="DELETE")
    
    def set_backend_state(self, name: str, state: str) -> APIResponse:
        """
        设置后端服务实例的运行状态（启动/停止）
        
        参数:
            name (str): 实例名称
            state (str): 实例状态，可选值为 'up' 或 'down'
            
        返回:
            APIResponse: API响应数据
        """
        payload = {"state": state}
        return self._request_api(f"v1/backends/{name}", payload, "PATCH")

    def get_backend(self, name: str) -> APIResponse:
        """
        获取指定实例的详细信息
        
        参数:
            name (str): 实例名称
            
        返回:
            APIResponse: 包含实例详情的响应数据
        """
        return self._request_api(f"v1/backends/{name}")

    def create_workflow(self, payload: WorkflowPayload) -> APIResponse:
        """
        创建一个新的工作流。
        
        参数:
            payload: 工作流配置参数
            
        返回:
            APIResponse: API响应数据
        """
        return self._request_api("v1/workflows", payload.to_dict(), "POST")

    def get_workflows(self) -> APIResponse:
        """
        获取所有可用的工作流列表
        
        返回:
            APIResponse: 包含工作流列表的响应数据
        """
        return self._request_api("v1/workflows")

    def get_workflow(self, workflow_id: str) -> APIResponse:
        """
        获取指定工作流的详细信息
        
        参数:
            workflow_id (str): 工作流ID
            
        返回:
            APIResponse: 包含工作流详情的响应数据
        """
        return self._request_api(f"v1/workflows/{workflow_id}")

    def update_workflow(self, workflow_id: str, payload: WorkflowPayload) -> APIResponse:
        """
        更新指定的工作流
        
        参数:
            workflow_id (str): 工作流ID
            payload: 更新的工作流配置
            
        返回:
            APIResponse: API响应数据
        """
        return self._request_api(f"v1/workflows/{workflow_id}", payload, "PATCH")

    def delete_workflow(self, workflow_id: str) -> APIResponse:
        """
        删除指定的工作流
        
        参数:
            workflow_id (str): 要删除的工作流ID
            
        返回:
            APIResponse: API响应数据
        """
        return self._request_api(f"v1/workflows/{workflow_id}", method="DELETE")

    def upload_file(self, file_path: str) -> APIResponse:
        """
        上传文件到ComfyOne
        
        参数:
            file_path (str): 要上传的文件路径
            
        返回:
            APIResponse: API响应数据
        """
        try:
            payload = {"file": open(file_path, "rb")}
        except FileNotFoundError:
            self.logger.error(f"File not found: {file_path}")
            raise FileNotFoundError(f"File not found: {file_path}")
        except Exception as e:
            self.logger.error(f"Error uploading file: {e}")
            raise e
        ret = self._request_api("v1/files", payload, "POST")
        # 关闭文件
        payload["file"].close()
        return ret

    def prompt(self, payload: PromptPayload) -> APIResponse:
        """
        向ComfyOne API发送prompt请求。
        
        参数:
            payload: Prompt请求参数
            
        返回:
            APIResponse: API响应数据
        """
        return self._request_api("v1/prompts", payload.to_dict(), "POST")

    def get_prompt_status(self, prompt_id: str) -> APIResponse:
        """
        获取指定prompt请求的状态
        
        参数:
            prompt_id (str): Prompt请求ID
            
        返回:
            APIResponse: 包含prompt状态的响应数据
        """
        return self._request_api(f"v1/prompts/{prompt_id}/status")

    def cancel_prompt(self, prompt_id: str) -> APIResponse:
        """
        取消正在执行的prompt请求
        
        参数:
            prompt_id (str): 要取消的Prompt请求ID
            
        返回:
            APIResponse: API响应数据
        """
        return self._request_api(f"v1/prompts/{prompt_id}/cancel", method="POST")
    
    def download_file(self, url: str, save_path: str = None) -> str:
        """
        从ComfyOne服务器下载文件
        
        参数:
            url (str): 文件下载URL
            save_path (str, optional): 文件保存路径。如果为None，将保存在当前目录下，使用URL中的文件名
            
        返回:
            str: 保存文件的完整路径
        """
        try:
            response = requests.get(url, headers=self.headers, stream=True)
            response.raise_for_status()
            
            # If save_path is not provided, extract filename from URL or use default name
            if save_path is None:
                from urllib.parse import urlparse
                from os.path import basename, splitext
                parsed_url = urlparse(url)
                url_filename = basename(parsed_url.path)
                
                # If URL doesn't have a filename or extension, use a default
                if not url_filename or not splitext(url_filename)[1]:
                    save_path = f"comfyone_download_{int(time.time())}.png"
                else:
                    save_path = url_filename
            else:
                save_path = os.path.join(save_path, url_filename)
            
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            self.logger.debug(f"File downloaded successfully to: {save_path}")
            return save_path
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error downloading file: {str(e)}")
            raise ConnectionError(f"Failed to download file: {str(e)}")
        except IOError as e:
            self.logger.error(f"Error saving file: {str(e)}")
            raise IOError(f"Failed to save file: {str(e)}")
    
    # TODO: 添加prompt历史记录的API