from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, UUID4

# Product Attribute Schema
class ProductAttributeSchema(BaseModel):
    id: UUID4
    product_id: UUID4
    name: str
    value: str

    class Config:
        orm_mode = True

# Product Schema
class ProductSchema(BaseModel):
    id: UUID4
    brand_id: UUID4
    name: str
    description: Optional[str] = None
    price: Optional[float] = None
    attributes: List[ProductAttributeSchema] = []

    class Config:
        orm_mode = True

# Brand Schema
class BrandSchema(BaseModel):
    id: UUID4
    name: str
    description: Optional[str] = None
    products: List[ProductSchema] = []

    class Config:
        orm_mode = True

# Message Schema
class MessageSchema(BaseModel):
    id: UUID4
    conversation_id: UUID4
    sender: str
    content: str
    created_at: datetime

    class Config:
        orm_mode = True

# Message Create Schema
class MessageCreate(BaseModel):
    content: str

# Conversation Schema
class ConversationSchema(BaseModel):
    id: UUID4
    brand_id: UUID4
    session_id: str
    created_at: datetime
    messages: List[MessageSchema] = []

    class Config:
        orm_mode = True

# LLM Request Schema
class LLMRequestSchema(BaseModel):
    brand_id: str
    conversation_id: str
    message: str

# LLM Response Schema
class LLMResponseSchema(BaseModel):
    response: str 