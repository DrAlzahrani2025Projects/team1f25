import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Chatbot")

st.title("Chatbot")

# Get API key from .env file or user input
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    api_key = st.text_input("Enter your Gemini API Key:", type="password")

if api_key:
    genai.configure(api_key=api_key)

    model = genai.GenerativeModel('gemini-2.0-flash')

    if "chat" not in st.session_state:
        st.session_state.chat = model.start_chat(history=[])

    # Display chat messages from history on app rerun
    for message in st.session_state.chat.history:
        with st.chat_message("assistant" if message.role == "model" else message.role):
            st.markdown(message.parts[0].text)

    # React to user input
    if prompt := st.chat_input("What is up?"):
        # Display user message in chat message container
        st.chat_message("user").markdown(prompt)
        
        try:
            # Send user message to Gemini and get response
            response = st.session_state.chat.send_message(prompt)
            
            # Display assistant response in chat message container
            with st.chat_message("assistant"):
                st.markdown(response.text)
        except Exception as e:
            st.chat_message("assistant").error(f"An error occurred: {e}")
else:
    st.warning("Please enter your Gemini API Key to continue.")