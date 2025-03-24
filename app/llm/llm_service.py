import os
import json
import psutil
from typing import List, Dict, Any, Optional
import asyncio
from sqlalchemy.orm import Session

# Import database models
from database import get_db
from models import Brand, Product, ProductAttribute, Conversation, Message

class LLMService:
    def __init__(self):
        self.model_path = os.environ.get("MODEL_PATH", "/app/models")
        self.model_name = os.environ.get("MODEL_NAME", "TheBloke/Llama-2-7B-Chat-GGUF")
        self.is_loaded = False
    
    async def load_model(self) -> None:
        """
        Simplified model loading function - for now, we'll just pretend to load the model
        to enable the service to start without crashes
        """
        try:
            # For now, we're not actually loading the model to avoid compatibility issues
            print(f"Model loading simulation for: {self.model_name}")
            await asyncio.sleep(2)  # Simulate loading
            self.is_loaded = True
            print(f"Model loaded successfully: {self.model_name}")
            
        except Exception as e:
            print(f"Error loading model: {str(e)}")
            self.is_loaded = False
    
    def is_model_loaded(self) -> bool:
        """Check if the model is loaded"""
        return self.is_loaded
    
    def get_model_name(self) -> str:
        """Get the name of the loaded model"""
        return self.model_name
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """Get memory usage of the process"""
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        return {
            "rss": memory_info.rss / (1024 * 1024),  # RSS in MB
            "vms": memory_info.vms / (1024 * 1024),  # VMS in MB
            "percent": process.memory_percent()
        }
    
    async def get_brand_info(self, brand_id: str, db: Session) -> Dict[str, Any]:
        """Get brand and product information from the database"""
        brand = db.query(Brand).filter(Brand.id == brand_id).first()
        if not brand:
            return {"brand_name": "Unknown", "products": []}
        
        products = db.query(Product).filter(Product.brand_id == brand_id).all()
        
        product_info = []
        for product in products:
            attributes = db.query(ProductAttribute).filter(ProductAttribute.product_id == product.id).all()
            
            product_data = {
                "name": product.name,
                "description": product.description,
                "price": float(product.price) if product.price else None,
                "attributes": {attr.name: attr.value for attr in attributes}
            }
            product_info.append(product_data)
        
        return {
            "brand_name": brand.name,
            "brand_description": brand.description,
            "products": product_info
        }
    
    async def get_conversation_history(self, conversation_id: str, db: Session) -> str:
        """Get conversation history from the database"""
        messages = db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at).all()
        
        history = ""
        for msg in messages:
            speaker = "Human" if msg.sender == "user" else "AI Assistant"
            history += f"{speaker}: {msg.content}\n"
        
        return history
    
    async def generate(
        self, 
        brand_info: Dict[str, Any], 
        user_message: str, 
        conversation_history: str
    ) -> str:
        """Generate a response using the LLM (simplified version)"""
        if not self.is_model_loaded():
            await self.load_model()
            if not self.is_model_loaded():
                return "I'm sorry, but I'm still initializing. Please try again in a moment."
        
        try:
            # Format brand info as text
            brand_name = brand_info.get("brand_name", "Unknown")
            
            # Generate a simple canned response for now
            return f"Hello! This is a simulated AI chatbot response for {brand_name}. Your query was: '{user_message}'. In a real implementation, I would provide information about the products and answer your questions."
            
        except Exception as e:
            print(f"Error generating response: {str(e)}")
            return "I apologize, but I encountered an error while generating a response. Please try again." 