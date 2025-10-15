# core/qroq_client.py
import os
from typing import List, Dict, Iterable, Optional, Union

# Import required modules and types
#
# Try to import Groq client
#     If import fails, raise error with install instructions
#
# Set default model, temperature, and max_tokens from environment variables
#
# Define function _as_messages(content, system)
#     If content is string:
#         Create user message dict
#     Else:
#         Use content as messages list
#     If system message provided:
#         Prepend system message
#     Return messages list
#
# Define class QroqClient:
#     On initialization:
#         Get API key from environment
#         If missing, raise error
#         Create Groq client with API key
#
#     Define chat method:
#         Prepare messages using _as_messages
#         Build payload with model, temperature, max_tokens, stream=False
#         Merge extra parameters if provided
#         Try to call Groq client for chat completion
#             Return assistant message content
#         If error, raise runtime error
#
#     Define chat_stream method:
#         Prepare messages using _as_messages
#         Build payload with model, temperature, max_tokens, stream=True
#         Merge extra parameters if provided
#         Try to call Groq client for streaming chat completion
#             For each chunk in stream:
#                 Extract delta content
#                 If present, yield delta
#         If error, raise runtime error
