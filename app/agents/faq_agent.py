from langchain_chroma import Chroma
from langchain_community.vectorstores import SupabaseVectorStore
from supabase.client import Client, create_client
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from app.agents.state import AgentState
from app.agents.prompts import FAQ_SYSTEM_PROMPT
from app.core.config import settings
import os
import logging

logger = logging.getLogger(__name__)

def get_embeddings(state: AgentState):
    """Initializes embeddings dynamically."""
    api_key = state.get("llm_api_key") or settings.openrouter_api_key
    base_url = state.get("llm_gateway") or "https://openrouter.ai/api/v1"
    return OpenAIEmbeddings(
        model="openai/text-embedding-3-small",
        api_key=api_key,
        base_url=base_url
    )

def get_llm(state: AgentState):
    """Initializes LLM dynamically."""
    model = state.get("llm_model") or "openai/gpt-4o-mini"
    base_url = state.get("llm_gateway") or "https://openrouter.ai/api/v1"
    api_key = state.get("llm_api_key") or settings.openrouter_api_key
    return ChatOpenAI(
        model=model,
        temperature=0,
        api_key=api_key,
        base_url=base_url,
        streaming=True
    )

def get_retriever():
    # If Supabase is configured, use it
    if settings.supabase_url and settings.supabase_service_key:
        supabase: Client = create_client(settings.supabase_url, settings.supabase_service_key)
        vectorstore = SupabaseVectorStore(
            client=supabase,
            embedding=embeddings,
            table_name="documents",
            query_name="match_documents"
        )
        return vectorstore.as_retriever(search_kwargs={"k": 3})
    
    # Fallback to local Chroma
    if os.path.exists("data/chroma"):
        vectorstore = Chroma(persist_directory="data/chroma", embedding_function=embeddings)
        return vectorstore.as_retriever(search_kwargs={"k": 3})
    
    return None

# Removed global llm

FAQ_PROMPT = ChatPromptTemplate.from_messages([
    ("system", FAQ_SYSTEM_PROMPT),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{question}")
])

from langchain_core.runnables import RunnableConfig

async def faq_node(state: AgentState, config: RunnableConfig):
    """Node to handle FAQ questions using RAG."""
    messages = state["messages"]
    if not messages:
        return {"messages": []}
        
    question = messages[-1].content
    logger.info(f"event=faq_node_started question='{question[:50]}...'")
    
    llm = get_llm(state)
    chain = FAQ_PROMPT | llm
    
    # Try to get cached retriever/embeddings from the app state
    # In LangGraph/FastAPI, we can't easily get 'app' here without passing it
    # We'll check if it's passed in the config or if we should fallback (backward compatibility)
    retriever = config.get("configurable", {}).get("retriever")
    
    if not retriever:
        # Fallback to dynamic initialization if not in cache (though we want to avoid this)
        logger.debug("event=faq_node_cache_miss action='dynamic_init'")
        
        def get_retriever_fallback(state):
            emb = get_embeddings(state)
            if settings.supabase_url and settings.supabase_service_key:
                supabase: Client = create_client(settings.supabase_url, settings.supabase_service_key)
                return SupabaseVectorStore(client=supabase, embedding=emb, table_name="documents", query_name="match_documents").as_retriever(search_kwargs={"k": 3})
            if os.path.exists("data/chroma"):
                return Chroma(persist_directory="data/chroma", embedding_function=emb).as_retriever(search_kwargs={"k": 3})
            return None
            
        retriever = get_retriever_fallback(state)
    
    history = messages[:-1]
    
    if not retriever:
        logger.warning("event=faq_node_fallback reason='No vector store available' action='using direct LLM with security prompt'")
        response = await chain.ainvoke({"context": "Nenhum contexto interno disponível no momento. Use apenas conhecimento de viagens e sua trava de segurança.", "question": question, "history": history}, config=config)
        return {"messages": [response]}
        
    docs = await retriever.ainvoke(question, config=config)
    logger.info(f"event=faq_node_retrieved_docs count={len(docs)}")
    context = "\n\n".join(doc.page_content for doc in docs)
    
    response = await chain.ainvoke({"context": context, "question": question, "history": history}, config=config)
    logger.info(f"event=faq_node_completed")
    
    return {"messages": [response]}
