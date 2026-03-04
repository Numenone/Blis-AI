import asyncio
import os
import sys
from langchain_core.messages import HumanMessage
from app.agents.orchestrator import get_graph
from langgraph.checkpoint.memory import MemorySaver

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

async def test_session_memory():
    print("Starting Session Memory & Personalization Test...")
    
    # Use in-memory checkpointer for testing
    memory = MemorySaver()
    graph = get_graph(checkpointer=memory)
    
    config = {"configurable": {"thread_id": "test_thread_123"}}
    
    # Step 1: Tell the bot our name and a preference
    print("\n--- Turn 1: Introduction ---")
    input_1 = {"messages": [HumanMessage(content="Olá! Meu nome é Felipe e eu pretendo viajar para Lisboa em breve. Gostaria de saber sobre as regras de bagagem.")]}
    async for event in graph.astream(input_1, config=config):
        for node, values in event.items():
            if "messages" in values:
                last_msg = values["messages"][-1].content
                print(f"[{node}]: {last_msg[:100]}...")
    
    # Step 2: Ask about history and name
    print("\n--- Turn 2: Testing Memory ---")
    input_2 = {"messages": [HumanMessage(content="O que eu te disse agora há pouco? E como eu me chamo?")]}
    final_response = ""
    async for event in graph.astream(input_2, config=config):
        for node, values in event.items():
            if "messages" in values:
                final_response = values["messages"][-1].content
                print(f"[{node}]: {final_response}")

    # Assertions
    print("\n--- Verification ---")
    name_remembered = "Felipe" in final_response
    topics_remembered = "Lisboa" in final_response or "bagagem" in final_response
    cordial = any(word in final_response.lower() for word in ["prazer", "felipe", "gentil", "olá", "entendo"])
    
    print(f"Remembered Name: {name_remembered}")
    print(f"Remembered Topics: {topics_remembered}")
    print(f"Cordial Tone: {cordial}")
    
    if name_remembered and topics_remembered:
        print("\nSUCCESS: Session memory and personalization are working!")
    else:
        print("\nFAILURE: Session memory might be missing.")

if __name__ == "__main__":
    asyncio.run(test_session_memory())
