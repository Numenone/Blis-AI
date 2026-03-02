from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import StreamingResponse
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage
from app.agents.orchestrator import get_graph
from app.core.config import settings
import json

import logging

router = APIRouter()
logger = logging.getLogger(__name__)

api_key_header = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Depends(api_key_header)):
    if api_key != settings.api_key:
        logger.warning("event=auth_failed reason='Invalid API Key provided'")
        raise HTTPException(
            status_code=403,
            detail="Could not validate credentials"
        )
    return api_key

class ChatRequest(BaseModel):
    session_id: str = Field(..., min_length=1, description="Unique identifier for the session to maintain state.")
    message: str = Field(..., min_length=1, description="The user's query or message.")
    stream: bool = Field(default=False, description="Set to true to receive an SSE stream of the response.")
    llm_model: str = Field(default="openai/gpt-4o-mini", description="LLM model identifier.")
    llm_gateway: str = Field(default="https://openrouter.ai/api/v1", description="LLM Gateway Base URL.")
    llm_api_key: str = Field(default="", description="API Key for the chosen LLM gateway. If empty, server defaults are used.")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "session_id": "test_session_123",
                    "message": "Qual é a política de bagagem?",
                    "llm_model": "openai/gpt-4o-mini",
                    "llm_gateway": "https://openrouter.ai/api/v1",
                    "llm_api_key": "sk-or-your-key-here",
                    "stream": False
                }
            ]
        }
    }

class ChatResponse(BaseModel):
    response: str = Field(..., description="The AI's generated response (only used when stream=false).")

async def generate_chat_stream(request: ChatRequest, fastapi_req: Request, checkpointer):
    """Generator for Server-Sent Events (SSE)."""
    logger.info(f"event=sse_stream_started session_id={request.session_id}")
    graph = get_graph(checkpointer)
    
    # Get cached components from app state
    retriever = getattr(fastapi_req.app.state, "retriever", None)
    embeddings = getattr(fastapi_req.app.state, "embeddings", None)
    
    config = {
        "configurable": {
            "thread_id": request.session_id,
            "retriever": retriever,
            "embeddings": embeddings
        }
    }
    
    # 1. IMMEDIATE FEEDBACK: Send a placeholder to reduce perceived latency
    yield f"data: {json.dumps({'content': 'Buscando informações...'})}\n\n"
    
    try:
        initial_state = {
            "messages": [HumanMessage(content=request.message)],
            "llm_model": request.llm_model,
            "llm_gateway": request.llm_gateway,
            "llm_api_key": request.llm_api_key
        }
        async for event in graph.astream_events(
            initial_state,
            config=config,
            version="v2"
        ):
            # logger.debug(f"event={event['event']} name={event.get('name')}")
            
            # Filter: only stream from agent nodes
            if event["event"] == "on_chat_model_stream":
                node_name = event.get("metadata", {}).get("langgraph_node", "")
                if node_name in ["faq_agent", "search_agent", "agent"]:
                    chunk = event["data"]["chunk"].content
                    if chunk:
                        data = json.dumps({"content": chunk})
                        yield f"data: {data}\n\n"
            
            # Diagnostic logs
            elif event["event"] == "on_node_start":
                logger.debug(f"node_started={event.get('name') or event.get('metadata', {}).get('langgraph_node')}")
        
        logger.info(f"event=sse_stream_completed session_id={request.session_id}")
        yield "data: [DONE]\n\n"
    except Exception as e:
        logger.error(f"event=sse_stream_error session_id={request.session_id} error={str(e)}")
        yield f"data: {json.dumps({'error': str(e)})}\n\n"
        yield "data: [DONE]\n\n"

@router.post(
    "/chat", 
    response_model=ChatResponse,
    summary="Interagir com os Agentes de Viagem (FAQ & Search)",
)
async def chat_endpoint(request: ChatRequest, fastapi_req: Request, api_key: str = Depends(verify_api_key)):
    logger.info(f"chat_endpoint: session_id={request.session_id} message='{request.message[:30]}...'")
    checkpointer = getattr(fastapi_req.app.state, "checkpointer", None)
    logger.info(f"chat_endpoint: session_id={request.session_id} cp_type={type(checkpointer)}")
    
    # Get cached components from app state for non-streaming case
    retriever = getattr(fastapi_req.app.state, "retriever", None)
    embeddings = getattr(fastapi_req.app.state, "embeddings", None)

    try:
        if request.stream:
            return StreamingResponse(
                generate_chat_stream(request, fastapi_req, checkpointer),
                media_type="text/event-stream"
            )

        logger.info(f"event=chat_invocation_started session_id={request.session_id}")
        graph = get_graph(checkpointer)
        
        config = {
            "configurable": {
                "thread_id": request.session_id,
                "retriever": retriever,
                "embeddings": embeddings
            }
        }
        
        # Invoke graph asynchronously
        initial_state = {
            "messages": [HumanMessage(content=request.message)],
            "llm_model": request.llm_model,
            "llm_gateway": request.llm_gateway,
            "llm_api_key": request.llm_api_key
        }
        result = await graph.ainvoke(
            initial_state,
            config=config
        )
        
        # The last message is the AI response
        final_message = result["messages"][-1].content
        logger.info(f"event=chat_invocation_completed session_id={request.session_id}")
        return ChatResponse(response=final_message)
    except Exception as e:
        logger.error(f"event=chat_invocation_error session_id={request.session_id} error={str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
@router.get("/api/history/{session_id}")
async def get_chat_history(session_id: str, fastapi_req: Request, api_key: str = Depends(verify_api_key)):
    checkpointer = getattr(fastapi_req.app.state, "checkpointer", None)
    logger.info(f"get_chat_history: session_id={session_id} cp_type={type(checkpointer)}")
    try:
        config = {"configurable": {"thread_id": session_id}}
        state_tuple = await checkpointer.aget_tuple(config)
        
        if not state_tuple:
            logger.info(f"event=history_not_found session_id={session_id}")
            return {"messages": []}
            
        checkpoint = state_tuple.checkpoint
        channel_values = checkpoint.get("channel_values", {})
        messages = channel_values.get("messages", [])
        
        logger.info(f"event=history_found session_id={session_id} msg_count={len(messages)} channels={list(channel_values.keys())}")
        
        # Format messages for frontend
        formatted_messages = []
        for msg in messages:
            content = ""
            role = "ai"
            msg_type = ""
            
            if hasattr(msg, "content"):
                content = msg.content
                msg_type = msg.type
            elif isinstance(msg, dict):
                content = msg.get("content", "")
                msg_type = msg.get("type", "")
            
            # Filter: only show human and AI messages, skip tools/system
            if msg_type == "human":
                role = "me"
            elif msg_type == "ai":
                role = "ai"
            else:
                continue # Skip ToolMessage, etc.

            if content:
                formatted_messages.append({"role": role, "content": content})
                
        return {"messages": formatted_messages}
    except Exception as e:
        logger.error(f"event=history_retrieval_error session_id={session_id} error={str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
