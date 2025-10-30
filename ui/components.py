# ui/components.py
import streamlit as st
from typing import Dict, Any
from core.services.result_formatter import ResultFormatter
from ui.theme import get_assistant_avatar, get_user_avatar

def render_sidebar():
    """Render the sidebar with app information and controls."""
    with st.sidebar:
        st.header("ℹ️ About")
        st.markdown("""
        This AI assistant helps you find scholarly resources by:
        1. Asking questions about your research needs
        2. Understanding your requirements
        3. Searching the CSUSB library database
        4. Presenting results in an organized table
        """)
        
        st.divider()
        
        st.header("💡 Tips")
        st.markdown("""
        - Simply tell me your research topic
        - Say "search now" to trigger an immediate search
        - Be specific about your subject area
        - Example: "I need articles about machine learning in healthcare"
        """)
        

        st.divider()
        new_search = st.button("🔄 Start New Search")

        st.divider()
        st.caption("🔬 Powered by Groq AI & CSUSB Library")

        return new_search


def render_chat_messages():
    for message in st.session_state.messages:
        if message["role"] == "assistant":
            avatar = get_assistant_avatar()
        elif message["role"] == "user":
            avatar = get_user_avatar()
        else:
            avatar = None

        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])


def display_results_table(results: Dict[str, Any]):
    """Display search results in a formatted table using ResultFormatter."""
    docs = results.get("docs", [])
    total_available = results.get("info", {}).get("total", 0)
    
    if not docs:
        st.warning("No results found. Try adjusting your search criteria.")
        return
    
    # Show info about results
    _display_result_count(len(docs), total_available)
    
    # Format data for table using ResultFormatter
    table_data = ResultFormatter.format_table_data(docs)
    
    # Display as dataframe with proper configuration
    st.dataframe(
        table_data,
        width='stretch',
        hide_index=True,
        column_config={
            "#": st.column_config.NumberColumn("#", width="small"),
            "Title": st.column_config.TextColumn("Title", width="large"),
            "Authors": st.column_config.TextColumn("Authors", width="medium"),
            "Year": st.column_config.TextColumn("Year", width="small"),
            "Type": st.column_config.TextColumn("Type", width="small"),
            "Link": st.column_config.LinkColumn(
                "Link",
                help="Click to view full record",
                display_text="🔗",
                width="small"
            )
        }
    )

# Display result count helper function
def _display_result_count(found: int, total: int):
    """Display information about result count."""
    if total > 0:
        if found < total and found < 10:
            st.info(f"Found {found} result(s) out of {total} available in the database.")
        else:
            st.success(f"Found {found} result(s)")
    else:
        st.success(f"Found {found} result(s)")


def display_search_results_section():
    """Display the search results section if results are available."""
    if st.session_state.search_results:
        with st.container():
            st.divider()
            st.subheader("🔍 Search Results")
            display_results_table(st.session_state.search_results)


def get_initial_greeting() -> str:
    """Get the initial greeting message."""
    return "Hello! What would you like to research today?"
