import asyncio
import os
import sys
from langchain_core.messages import HumanMessage
from app.agents.orchestrator import get_graph
from langgraph.checkpoint.memory import MemorySaver
from dotenv import load_dotenv

load_dotenv()

async def test_session_isolation():
    print("🧪 Testing Session Isolation...")
    memory = MemorySaver()
    graph = get_graph(checkpointer=memory)
    
    # Session 1: Identify as Felipe
    config_1 = {"configurable": {"thread_id": "session_felipe"}}
    print("\n--- Session 1: Felipe ---")
    await graph.ainvoke({"messages": [HumanMessage(content="Meu nome é Felipe.")]}, config=config_1)
    res1 = await graph.ainvoke({"messages": [HumanMessage(content="Qual meu nome?")]}, config=config_1)
    name_1 = res1["messages"][-1].content
    print(f"Response: {name_1}")
    
    # Session 2: New ID, should NOT know Felipe
    config_2 = {"configurable": {"thread_id": "session_anonymous"}}
    print("\n--- Session 2: Anonymous (New ID) ---")
    res2 = await graph.ainvoke({"messages": [HumanMessage(content="Qual meu nome?")]}, config=config_2)
    name_2 = res2["messages"][-1].content
    print(f"Response: {name_2}")
    
    # Verification
    s1_passed = "Felipe" in name_1
    s2_passed = "Felipe" not in name_2
    
    print(f"\nSession 1 remembers: {s1_passed}")
    print(f"Session 2 is isolated: {s2_passed}")
    
    if s1_passed and s2_passed:
        print("\n✅ SUCCESS: Sessions are correctly isolated!")
    else:
        print("\n❌ FAILURE: Session leakage detected or memory not working.")

if __name__ == "__main__":
    asyncio.run(test_session_isolation())
