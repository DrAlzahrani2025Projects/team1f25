# agents/rag_agent.py
from typing import Dict, Any
from core.embedding_model import Embedder
from core.chroma_client import get_collection, query
from core.qroq_client import QroqClient

# Define SYSTEM prompt for the AI assistant
#
# Define function rag_answer(question, top_k=6):
#     Create embedding model instance
#     Embed the question to get its vector
#     Get Chroma collection
#     Query the collection with the question vector for top_k results
#
#     For each hit in results:
#         Extract metadata (title, link)
#         Format context line with citation and text
#
#     Join context lines into a single context string
#
#     Create QroqClient instance
#     Build messages list with system and user messages (including context)
#     Call chat method on QroqClient with messages
#     Return dictionary with answer and hits
