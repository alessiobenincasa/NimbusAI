import os
import json
import psutil
from typing import List, Dict, Any, Optional
import asyncio
from sqlalchemy.orm import Session

# LangChain imports
from langchain.llms import HuggingFacePipeline
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory

# Hugging Face imports
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    pipeline,
    BitsAndBytesConfig
)

# Import database models
from database import get_db
from models import Brand, Product, ProductAttribute, Conversation, Message

class LLMService:
    def __init__(self):
        self.model_path = os.environ.get("MODEL_PATH", "/app/models")
        self.model_name = os.environ.get("MODEL_NAME", "TheBloke/Llama-2-7B-Chat-GGUF")
        self.model = None
        self.tokenizer = None
        self.llm = None
        self.chain = None
        self.is_loaded = False
    
    async def load_model(self) -> None:
        """Load the LLM model"""
        try:
            # Load in 4-bit quantization for efficiency
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype="float16"
            )
            
            # Load tokenizer and model
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                device_map="auto",
                quantization_config=quantization_config,
                cache_dir=self.model_path
            )
            
            # Create pipeline
            text_generation_pipeline = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                max_new_tokens=512,
                temperature=0.7,
                top_p=0.95,
                repetition_penalty=1.15
            )
            
            # Create LangChain LLM
            self.llm = HuggingFacePipeline(pipeline=text_generation_pipeline)
            
            # Create prompt template
            template = """
            You are a helpful AI assistant for the brand {brand_name}. You provide information about their products.
            
            Information about the brand:
            {brand_info}
            
            Chat History:
            {chat_history}
            
            Human: {human_input}
            AI Assistant:"""
            
            prompt = PromptTemplate(
                input_variables=["brand_name", "brand_info", "chat_history", "human_input"],
                template=template
            )
            
            # Create memory
            memory = ConversationBufferMemory(memory_key="chat_history")
            
            # Create chain
            self.chain = LLMChain(
                llm=self.llm,
                prompt=prompt,
                memory=memory,
                verbose=True
            )
            
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
        """Generate a response using the LLM"""
        if not self.is_model_loaded():
            await self.load_model()
            if not self.is_model_loaded():
                return "I'm sorry, but I'm still initializing. Please try again in a moment."
        
        try:
            # Format brand info as text
            brand_name = brand_info.get("brand_name", "Unknown")
            brand_desc = brand_info.get("brand_description", "")
            products = brand_info.get("products", [])
            
            brand_info_text = f"Brand: {brand_name}\nDescription: {brand_desc}\n\nProducts:\n"
            
            for product in products:
                brand_info_text += f"- {product['name']}: {product['description']}\n"
                brand_info_text += f"  Price: ${product.get('price', 'N/A')}\n"
                
                if product.get('attributes'):
                    brand_info_text += "  Features:\n"
                    for attr_name, attr_value in product['attributes'].items():
                        brand_info_text += f"    * {attr_name}: {attr_value}\n"
            
            # Generate response
            response = self.chain.run(
                brand_name=brand_name,
                brand_info=brand_info_text,
                chat_history=conversation_history,
                human_input=user_message
            )
            
            return response.strip()
            
        except Exception as e:
            print(f"Error generating response: {str(e)}")
            return "I apologize, but I encountered an error while generating a response. Please try again." 