from langchain_community.tools.tavily_search import TavilySearchResults
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
        base_url=base_url
    )
    search_tool = TavilySearchResults(max_results=3, tavily_api_key=settings.tavily_api_key)
    
    return create_react_agent(
        llm,
        tools=[search_tool],
        prompt=SEARCH_SYSTEM_PROMPT
    )

def search_node(state: AgentState):
    """Node to handle search queries using a ReAct agent."""
    messages = state["messages"]
    if not messages:
        return {"messages": []}
        
    question = messages[-1].content
    logger.info(f"event=search_node_started question='{question[:50]}...'")
    
    # Invoke the ReAct agent with the current conversation history
    react_agent = get_react_agent(state)
    result = react_agent.invoke({"messages": messages})
    
    # Extract only the newly generated messages to append to the state
    new_messages = result["messages"][len(messages):]
    logger.info(f"event=search_node_completed generated_messages={len(new_messages)}")
    
    return {"messages": new_messages}
