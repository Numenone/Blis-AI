import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from langgraph.checkpoint.redis import RedisSaver
import redis
from app.api.endpoints import router as api_router
from app.core.config import settings

# Setup structured logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Simple check to ensure Redis is available
    try:
        # Use from_conn_string for better compatibility with current langgraph patterns
        checkpointer = RedisSaver.from_conn_string(settings.redis_url)
        # Verify connection
        async with checkpointer.conn as conn:
            await conn.ping()
        logger.info("Successfully connected to Redis.")
        app.state.checkpointer = checkpointer
    except Exception as e:
        logger.warning(f"Could not connect to Redis: {e}")
        from langgraph.checkpoint.memory import MemorySaver
        logger.info("Falling back to MemorySaver for session persistence.")
        app.state.checkpointer = MemorySaver()
        
    yield

from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, FileResponse
import os

app = FastAPI(
    title="Blis AI - Multi-agent Travel Chatbot",
    description="API for the Blis AI technical test featuring LangGraph agents. Integrada com proteção API Key, CORS restrito e Security Headers contra ataques comuns (XSS, MIME Snipping e Framing).",
    version="1.0.0",
    lifespan=lifespan
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"event=validation_error method={request.method} path={request.url.path} detail={exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "message": "Erro de validação de tipagem forte (Pydantic)."},
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"event=internal_error method={request.method} path={request.url.path} error={str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error", "message": str(exc)},
    )
    
import time
from fastapi.middleware.cors import CORSMiddleware

# Security: Restrict CORS
# Note: You should specify your exact frontend domain instead of "*" in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://seu-front-end.vercel.app"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

@app.middleware("http")
async def security_headers(request: Request, call_next):
    # Extracted from standard secure application configurations
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(
        f"event=request_processed method={request.method} path={request.url.path} "
        f"status={response.status_code} duration={process_time:.4f}s"
    )
    return response

@app.get("/painel")
async def get_painel():
    static_file = os.path.join(os.path.dirname(__file__), "static", "index.html")
    return FileResponse(static_file)

app.include_router(api_router)
