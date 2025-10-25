# Quick Reference Guide - Scholar AI Assistant

## 📂 Where to Find Things

### Need to modify AI behavior?
→ **`core/ai_assistant.py`**
- Change conversation prompts
- Adjust search triggering logic
- Modify query extraction

### Need to change search functionality?
→ **`core/search_service.py`**
- Modify search parameters
- Change result parsing
- Add new result fields

### Need to update UI elements?
→ **`ui/components.py`**
- Modify sidebar content
- Change table display
- Update UI styling

### Need to adjust chat flow?
→ **`ui/chat_handler.py`**
- Change message handling
- Modify search execution flow
- Update error handling

### Need to add/modify session state?
→ **`ui/session_state.py`**
- Add new state variables
- Modify initialization
- Change reset behavior

### Need to change the main app structure?
→ **`app.py`**
- Modify page layout
- Change component order
- Update orchestration

## 🔧 Common Tasks

### Adding a New Feature

**Example: Add export to CSV functionality**

1. Add function to `ui/components.py`:
```python
def export_results_to_csv(results):
    # Implementation
    pass
```

2. Call from `app.py`:
```python
from ui.components import export_results_to_csv
# In display_search_results_section()
if st.button("Export to CSV"):
    export_results_to_csv(st.session_state.search_results)
```

### Modifying AI Prompts

**Location:** `core/ai_assistant.py`

**Function:** `generate_follow_up_question()` or `extract_search_query()`

Just edit the `system_prompt` or `prompt` variable.

### Changing Search Parameters

**Location:** `core/search_service.py`

**Function:** `perform_library_search()`

Modify the `limit` parameter or add new parameters.

### Updating UI Text

**Location:** `ui/components.py`

**Functions:** 
- `render_sidebar()` - Sidebar text
- `get_initial_greeting()` - Welcome message
- `display_results_table()` - Table headers/labels

## 🐛 Debugging

### Import Issues
```bash
python -m py_compile <filename.py>
```

### Test Specific Module
```python
# Test AI assistant
from core.ai_assistant import extract_search_query
from core.groq_client import GroqClient

client = GroqClient()
conversation = [{"role": "user", "content": "climate change"}]
print(extract_search_query(client, conversation))
```

### Check Session State
Add to `app.py`:
```python
with st.sidebar:
    st.write("Debug:", st.session_state)
```

## 📋 File Responsibilities Cheat Sheet

| File | What It Does | Edit When... |
|------|--------------|--------------|
| `app.py` | Main entry point | Changing overall app structure |
| `core/ai_assistant.py` | AI conversation logic | Modifying AI behavior |
| `core/search_service.py` | Search & parsing | Changing search/results |
| `ui/session_state.py` | State management | Adding new state variables |
| `ui/components.py` | UI elements | Updating UI appearance |
| `ui/chat_handler.py` | Chat flow | Changing conversation flow |

## 🎯 Module Dependencies

```
app.py
  ├─→ ui/session_state.py
  ├─→ ui/components.py
  │     └─→ core/search_service.py
  └─→ ui/chat_handler.py
        ├─→ core/groq_client.py
        ├─→ core/ai_assistant.py
        │     └─→ core/groq_client.py
        └─→ core/search_service.py
              └─→ core/csusb_library_client.py
```

## 💡 Best Practices

### 1. Keep Functions Focused
✅ One function = one responsibility
❌ Don't mix UI and business logic in one function

### 2. Use Proper Module
✅ UI code in `ui/`, business logic in `core/`
❌ Don't put business logic in UI modules

### 3. Import Only What You Need
✅ `from ui.components import render_sidebar`
❌ `from ui.components import *`

### 4. Test Core Logic Separately
✅ Test `core/` modules without Streamlit
❌ Don't require full app to test business logic

### 5. Document Your Changes
✅ Add docstrings to new functions
✅ Update this guide if structure changes

## 🚀 Running the App

```bash
# Development
streamlit run app.py

# Production (Docker)
./startup.sh
```

## 📊 Code Statistics

```bash
# Count lines in each module
wc -l app.py core/*.py ui/*.py

# Find TODOs
grep -r "TODO" core/ ui/ app.py

# Check for unused imports
pylint --disable=all --enable=unused-import app.py core/ ui/
```

---

**Remember:** The refactored structure makes the code easier to maintain, but the app works exactly the same way! 🎉
