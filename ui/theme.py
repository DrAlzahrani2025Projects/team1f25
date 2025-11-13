# ui/theme.py
import streamlit as st
import os

# Central color palette used across the app. Keys are descriptive so
# callers can reference colors by name when generating CSS.
CSUSB_COLORS = {
    "blue": "#0065BD",
    "black": "#000000",
    "gray": "#AAB0B5",
    "white": "#FFFFFF",
    "blue_dark": "#00509a",  # hover/pressed
}

def get_assistant_avatar() -> str | None:
    """Path to the assistant avatar image (fallback to emoji if missing)."""
    path = "ui/assests/chatbot-icon.png"   # keep your folder name
    return path if os.path.exists(path) else None

def get_user_avatar() -> str | None:
    """Path to the user avatar image (fallback to default emoji if missing)."""
    path = "ui/assests/coyote-icon.png"   # put your user icon here
    return path if os.path.exists(path) else None

def inject_brand_css():

    css = f"""
    <style>
      :root {{
        --csusb-blue: {CSUSB_COLORS["blue"]};
        --csusb-blue-dark: {CSUSB_COLORS["blue_dark"]};
        --csusb-black: {CSUSB_COLORS["black"]};
        --csusb-gray: {CSUSB_COLORS["gray"]};
        --csusb-white: {CSUSB_COLORS["white"]};
      }}

      /* Header title & subtitle */
      h1, .stMarkdown h1 {{
        color: var(--csusb-blue);
      }}

      /* Buttons */
      .stButton > button {{
        background: var(--csusb-blue);
        color: var(--csusb-white);
        border: 0;
        border-radius: 0.75rem;
      }}
      .stButton > button:hover {{
        background: var(--csusb-blue-dark);
      }}

      /* Sidebar headings */
      section[data-testid="stSidebar"] h1, 
      section[data-testid="stSidebar"] h2, 
      section[data-testid="stSidebar"] h3 {{
        color: var(--csusb-blue);
      }}

      /* Links */
      a, .st-emotion-cache-1wivap2 a {{
        color: var(--csusb-blue);
        text-decoration: none;
      }}
      a:hover {{
        text-decoration: underline;
      }}

      /* Dataframe header accent */
      div[data-testid="stDataFrame"] thead tr th {{
        border-bottom: 2px solid var(--csusb-blue);
      }}

      /* Chat bubbles */
      .stChatMessage.assistant {{
        background: rgba(170, 176, 181, 0.15); /* light CSUSB gray wash */
        border-left: 4px solid var(--csusb-blue);
        border-radius: 0.75rem;
      }}
      .stChatMessage.user {{
        background: rgba(0, 101, 189, 0.08); /* light blue wash */
        border-left: 4px solid var(--csusb-blue);
        border-radius: 0.75rem;
      }}

      /* Dividers – faint CSUSB gray */
      hr {{
        border: none;
        border-top: 1px solid rgba(170, 176, 181, 0.7);
      }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
