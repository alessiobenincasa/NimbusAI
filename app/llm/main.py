import os
import time
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from prometheus_client import Counter, Histogram, start_http_server
from typing import Dict, Any

# OpenTelemetry imports
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.exporter.prometheus import PrometheusMetricsExporter

# Local imports
from llm_service import LLMService
from database import get_db
from schemas import LLMRequest, LLMResponse

# Initialize LLM service
llm_service = LLMService()

# Initialize FastAPI
app = FastAPI(
    title="LLM Chatbot Service",
    description="LLM service for generating product-related responses",
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
INFERENCE_COUNT = Counter(
    "llm_inference_count", "Total count of LLM inferences"
)
INFERENCE_LATENCY = Histogram(
    "llm_inference_duration_seconds", "LLM inference latency in seconds"
)

# Initialize metrics server
@app.on_event("startup")
async def startup_event():
    # Start Prometheus HTTP server
    start_http_server(8002)
    # Load LLM model
    await llm_service.load_model()

# OpenTelemetry setup
resource = Resource(attributes={SERVICE_NAME: "llm-chatbot-llm"})
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
    
    return response

# Health check endpoint
@app.get("/health")
async def health_check():
    if llm_service.is_model_loaded():
        return {"status": "healthy", "model_loaded": True}
    return {"status": "starting", "model_loaded": False}

# Metrics endpoint
@app.get("/metrics")
async def metrics():
    return {}  # The Prometheus HTTP server handles this

# Generation endpoint
@app.post("/generate", response_model=LLMResponse)
async def generate_response(request: LLMRequest, db: Session = Depends(get_db)):
    start_time = time.time()
    
    try:
        # Get brand and product information from database
        brand_info = await llm_service.get_brand_info(request.brand_id, db)
        conversation_history = await llm_service.get_conversation_history(request.conversation_id, db)
        
        # Generate response
        response = await llm_service.generate(
            brand_info=brand_info,
            user_message=request.message,
            conversation_history=conversation_history
        )
        
        # Update metrics
        INFERENCE_COUNT.inc()
        INFERENCE_LATENCY.observe(time.time() - start_time)
        
        return LLMResponse(response=response)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Model status endpoint
@app.get("/model/status")
async def model_status():
    return {
        "model_loaded": llm_service.is_model_loaded(),
        "model_name": llm_service.get_model_name(),
        "memory_usage": llm_service.get_memory_usage()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 