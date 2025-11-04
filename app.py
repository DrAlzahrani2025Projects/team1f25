# app.py
"""
Scholar AI Assistant - Main Application Entry Point

A conversational AI chatbot that helps users discover academic resources
from the CSUSB library by understanding their research needs and presenting
results in an organized table format.

Refactored to follow SOLID principles (SRP, DIP, OCP) and KISS principle.
"""
import streamlit as st
from ui.session_state import initialize_session_state, reset_session_state
from ui.components import (
    render_sidebar,
    render_chat_messages,
    display_search_results_section,
    get_initial_greeting
)
from ui.chat_handler import initialize_groq_client, handle_user_message

# Configure the Streamlit page
st.set_page_config(
    page_title="Scholar AI Assistant",
    page_icon="📚",
    layout="wide"
)

# Main application class
class ScholarAIApp:
    """
    Main application class following SRP.
    Responsible only for application orchestration.
    """
    # Constructor
    def __init__(self):
        """Initialize the application."""
        self.groq_client = None
    # Setup method
    def setup(self) -> bool:
        """
        Setup application dependencies.
        Returns True if setup successful, False otherwise.
        """
        initialize_session_state()
        self.groq_client = initialize_groq_client()
        
        if not self.groq_client:
            st.warning("⚠️ Please set your GROQ_API_KEY environment variable to use this chatbot.")
            return False
        
        return True
    # Render header
    def render_header(self):
        """Render the application header."""
        st.title("📚 Scholar AI Assistant")
        st.markdown("*Your intelligent research companion for discovering academic resources*")
    # Handle sidebar actions
    def handle_sidebar_actions(self):
        """Handle sidebar interactions."""
        new_search = render_sidebar()
        # If Start New Search was clicked, reset and rerun
        if new_search:
            reset_session_state()
            st.rerun()

        # If sidebar signaled an action (apply/clear filters), handle rerun centrally
        action = st.session_state.get("sidebar_action")
        if action in ("apply", "clear"):
            # clear the flag and rerun to reflect changes
            st.session_state.pop("sidebar_action", None)
            st.rerun()
    
    def display_initial_greeting(self):
        """Display initial greeting if no messages exist."""
        if len(st.session_state.messages) == 0:
            initial_message = get_initial_greeting()
            st.session_state.messages.append({"role": "assistant", "content": initial_message})
            with st.chat_message("assistant"):
                st.markdown(initial_message)
    
    def handle_chat_input(self):
        """Handle user chat input."""
        if prompt := st.chat_input("Enter your research query..."):
            handle_user_message(prompt, self.groq_client)
    # Main run method
    def run(self):
        """Run the main application loop."""
        # Setup
        if not self.setup():
            return
        
        # Render UI
        self.render_header()
        self.handle_sidebar_actions()
        render_chat_messages()
        display_search_results_section()
        self.display_initial_greeting()
        
        # Handle input
        self.handle_chat_input()

# Application entry point
def main():
    """Application entry point - Keep it simple (KISS)."""
    app = ScholarAIApp()
    app.run()

# Entry point
if __name__ == "__main__":
    main()
