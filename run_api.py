import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from app.backend.api import app

"""
Script d'entrée pour lancer l'API FastAPI avec uvicorn, par exemple :

uvicorn run_api:app --reload
"""

