# Scholar AI Assistant - Architecture Documentation

## High-Level Architecture Diagram

```mermaid
graph LR
    User([👤 User])
    
    subgraph System["� Scholar AI Assistant"]
        UI["🖥️ Web Interface<br/>(Streamlit)"]
        AI["🧠 AI Engine<br/>(Conversation & Search)"]
    end
    
    LLM["🤖 Groq LLM<br/>(llama-3.3-70b)"]
    Library["📖 CSUSB Library<br/>(Primo Database)"]
    
    User <-->|"Natural Language<br/>Queries"| UI
    UI <-->|"Process &<br/>Display"| AI
    AI <-->|"Intent Analysis &<br/>Suggestions"| LLM
    AI <-->|"Search<br/>Academic Resources"| Library
    
    %% Styling
    classDef userStyle fill:#4CAF50,stroke:#2E7D32,stroke-width:3px,color:#fff
    classDef systemStyle fill:#2196F3,stroke:#1565C0,stroke-width:2px,color:#fff
    classDef externalStyle fill:#FF5722,stroke:#D84315,stroke-width:2px,color:#fff
    
    class User userStyle
    class UI,AI systemStyle
    class LLM,Library externalStyle
```

### 🎯 System Overview

**Scholar AI Assistant** is a conversational AI chatbot that helps users discover academic resources from the CSUSB library through natural language interactions.

| Component | Purpose |
|-----------|---------|
| **👤 User** | Researchers and students seeking academic resources |
| **🖥️ Web Interface** | Streamlit-based chat interface for user interaction |
| **🧠 AI Engine** | Processes queries, extracts parameters, executes searches |
| **🤖 Groq LLM** | Provides natural language understanding and generation |
| **📖 CSUSB Library** | Academic resource database (articles, books, journals) |

### 🔄 Simple Workflow

1. User asks a question in natural language
2. AI Engine analyzes intent using Groq LLM
3. AI Engine searches CSUSB Library database
4. Results displayed in organized table format
5. AI provides follow-up suggestions or clarifying questions

---

