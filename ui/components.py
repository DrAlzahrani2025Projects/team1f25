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
    
    if not docs:
        st.warning("No results found. Try adjusting your search criteria.")
        return
    
    st.success(f"Found {len(docs)} articles")
    
    # Prepare data for table
    table_data = []
    for idx, doc in enumerate(docs, 1):
        article = parse_article_data(doc)
        table_data.append({
            "#": idx,
            "Title": article["title"][:100] + "..." if len(article["title"]) > 100 else article["title"],
            "Author(s)": article["author"][:50] + "..." if len(article["author"]) > 50 else article["author"],
            "Year": article["date"],
            "Type": article["type"],
            "Source": article["source"][:40] + "..." if len(article["source"]) > 40 else article["source"],
            "DOI": article["doi"]
        })
    
    # Display as dataframe
    st.dataframe(table_data, use_container_width=True, hide_index=True)
    
    # Expandable details section
    with st.expander("📋 View Detailed Information"):
        for idx, doc in enumerate(docs, 1):
            article = parse_article_data(doc)
            st.markdown(f"### {idx}. {article['title']}")
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Author(s):** {article['author']}")
                st.write(f"**Publication Date:** {article['date']}")
                st.write(f"**Type:** {article['type']}")
                st.write(f"**Publisher:** {article['publisher']}")
            with col2:
                st.write(f"**Source:** {article['source']}")
                st.write(f"**ISSN:** {article['issn']}")
                st.write(f"**DOI:** {article['doi']}")
            st.divider()


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
