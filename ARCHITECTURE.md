# Scholar AI Assistant - Code Structure

## 📁 Project Structure

```
team1f25/
├── app.py                          # Main application entry point
├── core/                           # Core business logic
│   ├── ai_assistant.py            # AI conversation and query extraction
│   ├── csusb_library_client.py    # CSUSB library API client
│   ├── groq_client.py             # Groq LLM client wrapper
│   ├── logging_utils.py           # Logging utilities
│   └── search_service.py          # Search and result parsing
├── ui/                             # User interface components
│   ├── __init__.py                # UI module initializer
│   ├── chat_handler.py            # Chat interaction handler
│   ├── components.py              # Reusable UI components
│   └── session_state.py           # Session state management
├── requirements.txt                # Python dependencies
└── ARCHITECTURE.md                 # This file
```

## 🏗️ Module Overview

### **app.py**
- Main entry point for the Streamlit application
- Orchestrates UI components and chat handler
- Minimal logic - just coordinates modules
- ~70 lines (down from ~332 lines)

### **core/** - Business Logic Layer

#### **ai_assistant.py**
- Handles all AI conversation logic
- Functions:
  - `generate_follow_up_question()` - Generates contextual questions
  - `extract_search_query()` - Extracts search terms from conversation
  - `check_user_wants_search()` - Detects explicit search requests

#### **search_service.py**
- Manages library searches and result processing
- Functions:
  - `perform_library_search()` - Executes CSUSB library searches
  - `parse_article_data()` - Parses Primo API responses

#### **csusb_library_client.py**
- Low-level API client for CSUSB Primo library
- Handles HTTP requests, retries, and error handling

#### **groq_client.py**
- Wrapper for Groq LLM API
- Provides chat and streaming capabilities

### **ui/** - User Interface Layer

#### **session_state.py**
- Manages Streamlit session state
- Functions:
  - `initialize_session_state()` - Sets up initial state
  - `reset_session_state()` - Resets for new searches

#### **components.py**
- Reusable UI components
- Functions:
  - `render_sidebar()` - Sidebar with info and controls
  - `render_chat_messages()` - Displays chat history
  - `display_results_table()` - Formats and displays results
  - `display_search_results_section()` - Results container
  - `get_initial_greeting()` - Welcome message

#### **chat_handler.py**
- Handles chat interactions and flow control
- Functions:
  - `initialize_groq_client()` - Sets up LLM client
  - `handle_user_message()` - Processes user input
  - `handle_search_execution()` - Executes and displays searches

## 🔄 Data Flow

```
User Input (Streamlit)
    ↓
chat_handler.handle_user_message()
    ↓
ai_assistant.generate_follow_up_question() or check_user_wants_search()
    ↓
[If ready to search]
    ↓
ai_assistant.extract_search_query()
    ↓
search_service.perform_library_search()
    ↓
csusb_library_client.explore_search()
    ↓
search_service.parse_article_data()
    ↓
components.display_results_table()
    ↓
User sees results
```

## 🎯 Design Principles

### **Separation of Concerns**
- UI logic in `ui/` module
- Business logic in `core/` module
- Clear boundaries between layers

### **Single Responsibility**
- Each module has one clear purpose
- Functions are focused and testable
- Easy to locate and modify code

### **Maintainability**
- Modular structure allows easy updates
- Changes to UI don't affect business logic
- Can swap components independently

### **Testability**
- Pure functions without Streamlit dependencies in `core/`
- Easy to unit test business logic
- Mock-friendly architecture

## 🔧 Benefits of This Structure

1. **Easier Debugging**: Problems are isolated to specific modules
2. **Better Testing**: Core logic can be tested without UI
3. **Team Collaboration**: Multiple developers can work on different modules
4. **Code Reuse**: Core logic can be used in other interfaces (CLI, API, etc.)
5. **Scalability**: Easy to add new features without breaking existing code

## 📝 Adding New Features

### To add a new UI component:
1. Add function to `ui/components.py`
2. Import and use in `app.py`

### To add new AI capabilities:
1. Add function to `core/ai_assistant.py`
2. Use in `ui/chat_handler.py`

### To add new search features:
1. Add function to `core/search_service.py`
2. Use in `ui/chat_handler.py` or `ui/components.py`

## 🧪 Testing Strategy

```python
# Example: Testing core logic without UI
from core.ai_assistant import extract_search_query
from core.groq_client import GroqClient

def test_query_extraction():
    client = GroqClient()
    conversation = [
        {"role": "user", "content": "I need articles about climate change"}
    ]
    query = extract_search_query(client, conversation)
    assert "climate change" in query.lower()
```

## 🚀 Running the Application

```bash
streamlit run app.py
```

The modular structure doesn't change how the app runs - it just makes it much easier to maintain and extend!
