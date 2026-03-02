from langchain_community.vectorstores import Chroma
from langchain_community.vectorstores import SupabaseVectorStore
from supabase.client import Client, create_client
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.agents.state import AgentState
from app.agents.prompts import FAQ_SYSTEM_PROMPT
from app.core.config import settings
import os
import logging

logger = logging.getLogger(__name__)

embeddings = OpenAIEmbeddings(
    model="openai/text-embedding-3-small",
    api_key=settings.openrouter_api_key,
    base_url="https://openrouter.ai/api/v1"
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

llm = ChatOpenAI(
    model="openai/gpt-4o-mini", 
    temperature=0,
    api_key=settings.openrouter_api_key,
    base_url="https://openrouter.ai/api/v1"
)

FAQ_PROMPT = ChatPromptTemplate.from_messages([
    ("system", FAQ_SYSTEM_PROMPT),
    ("human", "{question}")
])

def faq_node(state: AgentState):
    """Node to handle FAQ questions using RAG."""
    messages = state["messages"]
    if not messages:
        return {"messages": []}
        
    question = messages[-1].content
    logger.info(f"event=faq_node_started question='{question[:50]}...'")
    
    retriever = get_retriever()
    chain = FAQ_PROMPT | llm
    
    if not retriever:
        logger.warning("event=faq_node_fallback reason='No vector store available' action='using direct LLM with security prompt'")
        response = chain.invoke({"context": "Nenhum contexto interno disponível no momento. Use apenas conhecimento de viagens e sua trava de segurança.", "question": question})
        return {"messages": [response]}
        
    docs = retriever.invoke(question)
    logger.info(f"event=faq_node_retrieved_docs count={len(docs)}")
    context = "\n\n".join(doc.page_content for doc in docs)
    
    response = chain.invoke({"context": context, "question": question})
    logger.info(f"event=faq_node_completed")
    
    return {"messages": [response]}
