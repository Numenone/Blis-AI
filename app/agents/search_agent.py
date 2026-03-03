from langchain_tavily import TavilySearch
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from app.agents.state import AgentState
from app.agents.prompts import SEARCH_SYSTEM_PROMPT

from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

def get_react_agent(state: AgentState):
    """Initializes ReAct agent dynamically."""
    model = state.get("llm_model") or "openai/gpt-4o-mini"
    base_url = state.get("llm_gateway") or "https://openrouter.ai/api/v1"
    api_key = state.get("llm_api_key") or settings.openrouter_api_key
    
    llm = ChatOpenAI(
        model=model,
        temperature=0,
        api_key=api_key,
        base_url=base_url,
        streaming=True
    )
    search_tool = TavilySearch(max_results=3, api_key=settings.tavily_api_key)
    
    return create_react_agent(
        llm,
        tools=[search_tool],
        prompt=SEARCH_SYSTEM_PROMPT
    )

from langchain_core.runnables import RunnableConfig

async def search_node(state: AgentState, config: RunnableConfig):
    """Node to handle search queries using a ReAct agent."""
    messages = state["messages"]
    if not messages:
        return {"messages": []}
        
    question = messages[-1].content
    logger.info(f"event=search_node_started question='{question[:50]}...'")
    
    # Invoke the ReAct agent with the current conversation history
    react_agent = get_react_agent(state)
    result = await react_agent.ainvoke({"messages": messages}, config=config)
    
    # Extract only the newly generated messages
    new_messages = result["messages"][len(messages):]
    
    # Filter to only get the final AIMessage (ignore ToolMessages and intermediate steps)
    final_response = None
    for m in reversed(new_messages):
        if m.type == "ai" and m.content:
            final_response = m
            break
            
    if final_response:
        logger.info(f"event=search_node_completed final_msg_len={len(final_response.content)}")
        return {"messages": [final_response]}
    
    logger.warning("event=search_node_no_final_response")
    return {"messages": []}
