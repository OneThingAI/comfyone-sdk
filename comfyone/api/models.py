from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field, validator
from enum import Enum
from .exceptions import ValidationError


class IOType(str, Enum):
    """工作流输入输出类型枚举"""
    IMAGE = "image"
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"

class WorkflowInput(BaseModel):
    """工作流输入参数配置"""
    id: str
    type: IOType
    name: str

    def to_dict(self) -> Dict[str, Any]:
        """将输入参数配置转换为字典"""
        return self.dict()

class WorkflowInputPayload(BaseModel):
    """工作流输入参数配置集合"""
    inputs: List[WorkflowInput]

    def to_dict(self) -> List[Dict[str, Any]]:
        """将工作流输入参数配置集合转换为字典列表"""
        return [input.to_dict() for input in self.inputs]

class WorkflowOutput(BaseModel):
    """工作流输出参数配置"""
    id: str

    def to_dict(self) -> str:
        """将输出参数配置转换为字符串"""
        return self.id

class WorkflowOutputPayload(BaseModel):
    """工作流输出参数配置集合"""
    outputs: List[WorkflowOutput]

    def to_dict(self) -> List[str]:
        """将工作流输出参数配置集合转换为字符串列表"""
        return [output.to_dict() for output in self.outputs]

class WorkflowPayload(BaseModel):
    """工作流创建请求负载"""
    name: str = Field(..., min_length=1, description="工作流名称")
    inputs: WorkflowInputPayload
    outputs: WorkflowOutputPayload
    workflow: Dict[str, Any]

    @validator('workflow')
    def workflow_must_be_dict(cls, v):
        """验证workflow字段必须为字典"""
        if not isinstance(v, dict):
            raise ValidationError("workflow必须是一个字典")
        return v

    def to_dict(self) -> Dict[str, Any]:
        """将WorkflowPayload转换为字典"""
        return {
            'name': self.name,
            'inputs': self.inputs.to_dict(),
            'outputs': self.outputs.to_dict(),
            'workflow': self.workflow
        }

    class Config:
        """pydantic配置"""
        str_strip_whitespace = True
        validate_assignment = True

class PromptInput(BaseModel):
    """Prompt输入配置"""
    id: str = Field(..., min_length=1, description="输入ID")
    params: Dict[str, Any] = Field(..., description="输入参数")

    def to_dict(self) -> Dict[str, Any]:
        """将PromptInput转换为字典"""
        return self.dict()


class PromptPayload(BaseModel):
    """Prompt请求负载"""
    workflow_id: str = Field(..., min_length=1, description="工作流ID") 
    inputs: List[PromptInput] = Field(..., description="输入参数列表")
    free_cache: bool = False
    free_gpu: bool = True
    backend: Optional[str] = None

    @validator('inputs')
    def validate_inputs(cls, v):
        """验证inputs列表中的每个元素都是PromptInput类型"""
        if not all(isinstance(x, PromptInput) for x in v):
            raise ValidationError("inputs列表中的所有元素必须是PromptInput类型")
        return v

    def to_dict(self) -> Dict[str, Any]:
        """将PromptPayload转换为字典"""
        return {
            'workflow_id': self.workflow_id,
            'inputs': [input.to_dict() for input in self.inputs],
            'free_cache': self.free_cache
        }

    class Config:
        """pydantic配置"""
        str_strip_whitespace = True
        validate_assignment = True 

class APIResponse(BaseModel):
    """API响应基础结构"""
    code: int
    msg: str
    data: Optional[Union[Dict[str, Any], List[Any]]] = None

    def to_dict(self) -> Dict[str, Any]:
        """将API响应转换为字典"""
        return self.dict()


