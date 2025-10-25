# ui/components.py
"""
UI components for the Streamlit application.
"""
import streamlit as st
from typing import Dict, Any
from core.search_service import parse_article_data


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
        st.caption("Powered by Groq AI & CSUSB Library")
        
        return new_search


def render_chat_messages():
    """Render all chat messages from session state."""
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


def display_results_table(results: Dict[str, Any]):
    """Display search results in a formatted table."""
    docs = results.get("docs", [])
    total_available = results.get("info", {}).get("total", 0)
    
    if not docs:
        st.warning("No results found. Try adjusting your search criteria.")
        return
    
    # Show info message if fewer results than expected
    if total_available > 0:
        if len(docs) < total_available and len(docs) < 10:
            st.info(f"Found {len(docs)} result(s) out of {total_available} available in the database.")
        else:
            st.success(f"Found {len(docs)} result(s)")
    else:
        st.success(f"Found {len(docs)} result(s)")
    
    # Prepare data for table with clickable links
    table_data = []
    for idx, doc in enumerate(docs, 1):
        article = parse_article_data(doc)
        
        # Get the link URL
        link = article.get("link", "")
        
        table_data.append({
            "#": idx,
            "Title": article["title"][:80] + "..." if len(article["title"]) > 80 else article["title"],
            "Authors": article["author"][:40] + "..." if len(article["author"]) > 40 else article["author"],
            "Year": article["date"],
            "Type": article["type"],
            "Link": link if link else None
        })
    
    # Display as dataframe
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


def display_search_results_section():
    """Display the search results section if results are available."""
    if st.session_state.search_results:
        with st.container():
            st.divider()
            st.subheader("🔍 Search Results")
            display_results_table(st.session_state.search_results)


def get_initial_greeting() -> str:
    """Get the initial greeting message."""
    return "Hello! I'm your Scholar AI Assistant. I'll help you find academic resources like articles, research papers, books, and journals. What would you like to research today?"
