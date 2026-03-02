import operator
from typing import Annotated, TypedDict
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], operator.add]
    session_id: str
    next_node: str
    llm_model: str
    llm_gateway: str
    llm_api_key: str
