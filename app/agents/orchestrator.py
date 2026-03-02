from typing import Literal
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END
from app.agents.state import AgentState
from app.agents.faq_agent import faq_node
from app.agents.search_agent import search_node
from app.agents.prompts import ROUTER_SYSTEM_PROMPT

import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

# Provedor de LLM via OpenRouter (para unificar acesso a modelos como GPT-4o, Claude, etc)
def get_llm(state: AgentState):
    """Initializes LLM dynamically based on state."""
    model = state.get("llm_model") or "openai/gpt-4o-mini"
    base_url = state.get("llm_gateway") or "https://openrouter.ai/api/v1"
    api_key = state.get("llm_api_key") or settings.openrouter_api_key
    
    return ChatOpenAI(
        model=model,
        temperature=0,
        api_key=api_key,
        base_url=base_url
    )

class RouteDecision(BaseModel):
    destination: Literal["faq_agent", "search_agent"] = Field(
        description="Destino para a pergunta. 'faq_agent' para políticas de bagagem, check-in, documentação e regras. 'search_agent' para passagens, conexões, hotéis, clima atual, e dados em tempo real."
    )

router_prompt = ChatPromptTemplate.from_messages([
    ("system", ROUTER_SYSTEM_PROMPT),
    ("human", "{question}")
])

def route_question(state: AgentState):
    """Router node that decides which agent to call next."""
    messages = state["messages"]
    if not messages:
        logger.warning("event=router_decision reason='No messages' destination='faq_agent'")
        return {"next_node": "faq_agent"} # Default
        
    question = messages[-1].content
    logger.info(f"event=router_evaluating question='{question[:50]}...'")
    
    llm = get_llm(state)
    router_chain = router_prompt | llm.with_structured_output(RouteDecision)
    decision = router_chain.invoke({"question": question})
    
    logger.info(f"event=router_decision destination={decision.destination}")
    return {"next_node": decision.destination}

def router_edge(state: AgentState) -> str:
    """Conditional edge based on the routing decision."""
    return state["next_node"]

# Build graph
builder = StateGraph(AgentState)
builder.add_node("router", route_question)
builder.add_node("faq_agent", faq_node)
builder.add_node("search_agent", search_node)

builder.add_edge(START, "router")
builder.add_conditional_edges("router", router_edge)
builder.add_edge("faq_agent", END)
builder.add_edge("search_agent", END)

def get_graph(checkpointer=None):
    if checkpointer:
        return builder.compile(checkpointer=checkpointer)
    return builder.compile()
