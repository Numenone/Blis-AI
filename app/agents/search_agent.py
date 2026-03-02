from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from app.agents.state import AgentState
from app.agents.prompts import SEARCH_SYSTEM_PROMPT

from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Initialize LLM via OpenRouter and tools
llm = ChatOpenAI(
    model="openai/gpt-4o-mini", 
    temperature=0,
    api_key=settings.openrouter_api_key,
    base_url="https://openrouter.ai/api/v1"
)
search_tool = TavilySearchResults(max_results=3, tavily_api_key=settings.tavily_api_key)

# Create a prebuilt ReAct agent that can use tools
system_prompt = SEARCH_SYSTEM_PROMPT

react_agent = create_react_agent(
    llm,
    tools=[search_tool],
    prompt=system_prompt
)

def search_node(state: AgentState):
    """Node to handle search queries using a ReAct agent."""
    messages = state["messages"]
    if not messages:
        return {"messages": []}
        
    question = messages[-1].content
    logger.info(f"event=search_node_started question='{question[:50]}...'")
    
    # Invoke the ReAct agent with the current conversation history
    result = react_agent.invoke({"messages": messages})
    
    # Extract only the newly generated messages to append to the state
    new_messages = result["messages"][len(messages):]
    logger.info(f"event=search_node_completed generated_messages={len(new_messages)}")
    
    return {"messages": new_messages}
