from pydantic import BaseModel, UUID4
from typing import Optional, List, Dict, Any

class LLMRequest(BaseModel):
    brand_id: str
    conversation_id: str
    message: str

class LLMResponse(BaseModel):
    response: str

class ModelInfo(BaseModel):
    model_loaded: bool
    model_name: str
    memory_usage: Dict[str, float] 