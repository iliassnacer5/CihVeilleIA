import asyncio
import sys
import time

# Fix for Windows asyncio loop
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import torch # Ensure torch is imported
import os

# Force transformers to use PyTorch
os.environ["TRANSFORMERS_VERBOSITY"] = "info"
os.environ["USE_TORCH"] = "1"

from app.nlp.banking_nlp import BankingNlpService

async def test_models():
    print("Testing BankingNlpService with new reliable models...")
    start_time = time.time()
    
    try:
        # Initialize service (lazy loading enabled)
        nlp = BankingNlpService()
        
        test_text_fr = """
        CIH Bank a annoncé ses résultats annuels avec une forte croissance de l'activité. 
        La banque continue d'investir dans le digital et l'intelligence artificielle pour améliorer l'expérience client.
        Le risque de crédit est resté sous contrôle malgré un contexte économique difficile.
        """
        
        print("\n1. Testing Classification (French)...")
        # Trigger lazy loading
        classifications = nlp.classify_documents([test_text_fr])
        res = classifications[0]
        print(f"Label: {res.label}, Score: {res.score:.4f}")
        
        print("\n2. Testing Summarization (French)...")
        summaries = nlp.summarize_documents([test_text_fr], max_length=100, min_length=20)
        print(f"Summary: {summaries[0].summary}")
        
    except Exception as e:
        print(f"\n[ERROR] An error occurred: {e}")
        import traceback
        traceback.print_exc()
    
    end_time = time.time()
    print(f"\nTotal time: {end_time - start_time:.2f}s")

if __name__ == "__main__":
    asyncio.run(test_models())
