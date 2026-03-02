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

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "session_id": "test_session_123",
                    "message": "Qual é a política de bagagem para voos internacionais?",
                    "stream": False
                }
            ]
        }
    }

class ChatResponse(BaseModel):
    response: str = Field(..., description="The AI's generated response (only used when stream=false).")

async def generate_chat_stream(request: ChatRequest, checkpointer):
    """Generator for Server-Sent Events (SSE)."""
    logger.info(f"event=sse_stream_started session_id={request.session_id}")
    graph = get_graph(checkpointer)
    config = {"configurable": {"thread_id": request.session_id}}
    
    try:
        async for event in graph.astream_events(
            {"messages": [HumanMessage(content=request.message)]},
            config=config,
            version="v2"
        ):
            if event["event"] == "on_chat_model_stream":
                node_name = event.get("metadata", {}).get("langgraph_node", "")
                if node_name in ["faq_agent", "search_agent", "agent"]:
                    chunk = event["data"]["chunk"].content
                    if chunk:
                        data = json.dumps({"content": chunk})
                        yield f"data: {data}\n\n"
        
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
    description="""
    Envia uma mensagem para o Orquestrador da Blis AI.
    
    O orquestrador pode escolher entre:
    - **FAQ Agent**: Para responder dúvidas sobre políticas de bagagem usando a base de conhecimento (RAG).
    - **Search Agent**: Para buscar informações em tempo real na internet (Tavily).
    
    **Como testar aqui no Swagger**:
    1. Clique no botão "Authorize" no topo da página e insira a sua API Key (padrão: `blis_secret_token_123`).
    2. Clique em "Try it out".
    3. O body (`ChatRequest`) já estará preenchido com um exemplo de payload.
    4. Digite a sua pergunta no campo `message`. 
    5. Se quiser testar o Node de Web Search, digite por exemplo "Qual o clima em Paris hoje?".
    6. Se quiser testar o RAG, use "Quais as regras de check-in?".
    7. (Opcional) Altere `"stream": true` se o seu cliente suportar SSE.
    """
)
async def chat_endpoint(request: ChatRequest, fastapi_req: Request, api_key: str = Depends(verify_api_key)):
    try:
        checkpointer = fastapi_req.app.state.checkpointer
        if request.stream:
            return StreamingResponse(
                generate_chat_stream(request, checkpointer),
                media_type="text/event-stream"
            )

        logger.info(f"event=chat_invocation_started session_id={request.session_id}")
        graph = get_graph(checkpointer)
        
        config = {"configurable": {"thread_id": request.session_id}}
        
        # Invoke graph asynchronously
        result = await graph.ainvoke(
            {"messages": [HumanMessage(content=request.message)]},
            config=config
        )
        
        # The last message is the AI response
        final_message = result["messages"][-1].content
        logger.info(f"event=chat_invocation_completed session_id={request.session_id}")
        return ChatResponse(response=final_message)
    except Exception as e:
        logger.error(f"event=chat_invocation_error session_id={request.session_id} error={str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
