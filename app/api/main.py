import os
import time
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from prometheus_client import Counter, Histogram, start_http_server
from typing import List, Optional

# OpenTelemetry imports
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# Local imports
from models import Brand, Product, Conversation, Message
from database import get_db, init_db
from schemas import BrandSchema, ProductSchema, MessageCreate, ConversationSchema, MessageSchema

# Initialize FastAPI
app = FastAPI(
    title="LLM Chatbot API",
    description="API for LLM-based conversational product chatbot",
    version="1.0.0",
)

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Metrics
REQUEST_COUNT = Counter(
    "http_requests_total", "Total count of HTTP requests", ["method", "endpoint", "status_code"]
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds", "HTTP request latency in seconds", ["method", "endpoint"]
)

# Initialize database
@app.on_event("startup")
async def startup_event():
    init_db()
    # Start Prometheus HTTP server
    start_http_server(8001)

# OpenTelemetry setup
resource = Resource(attributes={SERVICE_NAME: "llm-chatbot-api"})
tracerprovider = TracerProvider(resource=resource)
trace.set_tracer_provider(tracerprovider)

# Instrument FastAPI
FastAPIInstrumentor.instrument_app(app)

# Middleware for metrics
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    latency = time.time() - start_time
    
    REQUEST_COUNT.labels(
        method=request.method, 
        endpoint=request.url.path, 
        status_code=response.status_code
    ).inc()
    
    REQUEST_LATENCY.labels(
        method=request.method, 
        endpoint=request.url.path
    ).observe(latency)
    
    return response

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Metrics endpoint
@app.get("/metrics")
async def metrics():
    return {}  # The Prometheus HTTP server handles this

# Brand endpoints
@app.get("/brands", response_model=List[BrandSchema])
async def get_brands(db: Session = Depends(get_db)):
    return db.query(Brand).all()

@app.get("/brands/{brand_id}", response_model=BrandSchema)
async def get_brand(brand_id: str, db: Session = Depends(get_db)):
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    return brand

# Product endpoints
@app.get("/brands/{brand_id}/products", response_model=List[ProductSchema])
async def get_products(brand_id: str, db: Session = Depends(get_db)):
    products = db.query(Product).filter(Product.brand_id == brand_id).all()
    return products

@app.get("/products/{product_id}", response_model=ProductSchema)
async def get_product(product_id: str, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

# Conversation endpoints
@app.post("/brands/{brand_id}/conversations", response_model=ConversationSchema)
async def create_conversation(brand_id: str, db: Session = Depends(get_db)):
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    # Create a new conversation
    session_id = f"session_{int(time.time())}"
    conversation = Conversation(brand_id=brand_id, session_id=session_id)
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    
    return conversation

@app.post("/conversations/{conversation_id}/messages")
async def create_message(
    conversation_id: str, 
    message: MessageCreate, 
    db: Session = Depends(get_db)
):
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Save user message
    db_message = Message(
        conversation_id=conversation_id,
        sender="user",
        content=message.content
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)  # Refresh to get the ID and created_at
    
    # Call LLM service for response
    import httpx
    
    llm_service_url = os.environ.get("LLM_SERVICE_URL", "http://llm:8001")
    brand_id = conversation.brand_id
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{llm_service_url}/generate",
                json={
                    "brand_id": str(brand_id),
                    "conversation_id": conversation_id,
                    "message": message.content
                },
                timeout=60.0
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail="Error from LLM service")
            
            llm_response = response.json()
            
            # Save AI response
            ai_message = Message(
                conversation_id=conversation_id,
                sender="ai",
                content=llm_response["response"]
            )
            db.add(ai_message)
            db.commit()
            db.refresh(ai_message)  # Refresh to get the ID and created_at
            
            # Convert the SQLAlchemy objects to Pydantic models for proper JSON serialization
            user_message_schema = MessageSchema.from_orm(db_message)
            ai_message_schema = MessageSchema.from_orm(ai_message)
            
            return {
                "user_message": user_message_schema,
                "ai_response": ai_message_schema
            }
    
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="LLM service unavailable")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 