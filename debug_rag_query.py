
import asyncio
from app.rag.pipeline import RagPipeline
from app.rag.chatbot import RagChatbot
from app.search.semantic_search import SemanticSearchEngine, SearchFilters

QUERY = "Stratégie Data Strategy LightGrey"

async def debug_rag():
    print(f"--- Debugging RAG for query: '{QUERY}' ---")
    
    # 1. Test Semantic Search directly (to see raw scores)
    print("\n[1] Testing Semantic Search Engine:")
    search_engine = SemanticSearchEngine()
    results = await search_engine.vector_search(QUERY, top_k=5)
    
    if not results:
        print("❌ No results found in Semantic Search.")
    else:
        print(f"✅ Found {len(results)} results.")
        for i, r in enumerate(results):
            print(f"   {i+1}. Score: {r.score:.4f} | Title: {r.title}")
            print(f"      Ctx: {r.text_snippet[:100]}...")

    # 2. Test Chatbot Logic (to see if it blocks)
    print("\n[2] Testing Chatbot Answer Logic:")
    chatbot = RagChatbot(search_engine=search_engine)
    
    # Check threshold logic manually
    if results:
        best_score = float(results[0].score)
        print(f"   Best Score: {best_score}")
        print(f"   Min Threshold: {chatbot.min_vector_score}")
        
        if best_score < 0.01:
            print("❌ BLOCKED by min_vector_score threshold (0.01).")
        else:
            print("✅ PASSED min_vector_score threshold (0.01).")
            
        if len(results) < chatbot.min_documents:
             print(f"❌ BLOCKED by min_documents threshold ({len(results)} < {chatbot.min_documents}).")
        else:
             print("✅ PASSED min_documents threshold.")
             
    answer = await chatbot.answer(QUERY)
    print("\n[3] Final Chatbot Response:")
    print(f"   Answer: {answer.answer}")
    print(f"   Reason: {answer.reason}")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(debug_rag())
