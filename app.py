# app.py
import os
import base64
import glob
import streamlit as st

from ui.session_state import initialize_session_state, reset_session_state
from ui.components import (
    render_sidebar,
    render_chat_messages,
    display_search_results_section,
    get_initial_greeting,
)
from ui.chat_handler import initialize_groq_client, handle_user_message
from ui.theme import inject_brand_css, get_assistant_avatar  # CSUSB brand colors & UI polish

# -----------------------------------------------------------------------------
# Logo resolution helpers
# -----------------------------------------------------------------------------

CANDIDATE_DIRS = [
    ".",                 # repo root
    "ui/assets",
    "ui/assests",        # common typo just in case
    "assets",
    "static",
]
CANDIDATE_NAMES = [
    "CSU_San_Bernardino_seal",
    "csusb_logo",
    "csusb",
    "logo",
    "seal",
    "csusb_logo-main_LIBRARY",
]
CANDIDATE_EXTS = [".png", ".jpg", ".jpeg", ".svg", ".webp"]


def resolve_logo_path() -> str | None:
    # 1) Environment override
    env_path = "ui/assets/csusb_logo-main_LIBRARY.png"
    if env_path and os.path.exists(env_path):
        return os.path.abspath(env_path)

    # 2) Try exact known paths (most recent one you used)
    exacts = [
        "ui/assets/csusb_logo-main_LIBRARY.png",
        "ui/assets/CSU_San_Bernardino_seal.png",
        "ui/assets/csusb_logo.png"
    ]
    for p in exacts:
        if os.path.exists(p):
            return os.path.abspath(p)

    # 3) Glob search
    for d in CANDIDATE_DIRS:
        for name in CANDIDATE_NAMES:
            for ext in CANDIDATE_EXTS:
                pat = os.path.join(d, f"{name}*{ext}")
                matches = glob.glob(pat)
                if matches:
                    return os.path.abspath(matches[0])

    return None


def data_uri_for_image(path: str | None) -> str | None:
    """Return a base64 data URI for a local image path."""
    if not path or not os.path.exists(path):
        return None
    try:
        with open(path, "rb") as f:
            raw = f.read()
        b64 = base64.b64encode(raw).decode("utf-8")
        ext = os.path.splitext(path)[1].lower()
        mime = (
            "image/png" if ext == ".png"
            else "image/jpeg" if ext in [".jpg", ".jpeg"]
            else "image/svg+xml" if ext == ".svg"
            else "image/webp" if ext == ".webp"
            else "application/octet-stream"
        )
        return f"data:{mime};base64,{b64}"
    except Exception:
        return None


# -----------------------------------------------------------------------------
# Streamlit page setup
# -----------------------------------------------------------------------------

st.set_page_config(
    page_title="Scholar AI Assistant",
    page_icon="ui/assests/CodyCoyote_head-smile_cmyk.svg",
    layout="wide",
)

inject_brand_css()  # CSUSB palette


class ScholarAIApp:
    """Main application class following SRP."""
# Constructor
    def __init__(self):
        self.groq_client = None
        self._header_css_injected = False

    def setup(self) -> bool:
        """Setup application dependencies."""
        initialize_session_state()
        self.groq_client = initialize_groq_client()
        if not self.groq_client:
            st.warning("⚠️ Please set your GROQ_API_KEY environment variable to use this chatbot.")
            return False
        return True

    def _inject_header_css_once(self):
        """Inject responsive header CSS only once per session."""
        if self._header_css_injected:
            return
        self._header_css_injected = True

        st.markdown(
            """
            <style>
              .csusb-hero {
                display: flex;
                align-items: center;           /* vertical align logo & text */
                justify-content: center;       /* center the whole group */
                gap: 16px;
                margin: 8px 0 4px 0;
                flex-wrap: wrap;               /* wrap on small screens */
                text-align: center;            /* default centered when wrapped */
              }
              .csusb-hero-left {
                display: flex;
                align-items: center;
                justify-content: center;
              }
              .csusb-logo {
                height: 100px;
                width: auto;
                object-fit: contain;
                margin-top: 7px;
              }
              .csusb-hero-text h2 {
                color: #0065BD;                /* CSUSB blue */
                margin: 0;
                font-weight: 700;
              }
              .csusb-hero-text p {
                margin: 6px 0 0 0;
              }
              @media (min-width: 740px) {
                .csusb-hero-text { text-align: left; }
              }
            </style>
            """,
            unsafe_allow_html=True,
        )

    def render_header(self):
        """Render the application header with CSUSB logo and branding."""
        self._inject_header_css_once()

        logo_path = resolve_logo_path()
        data_uri = data_uri_for_image(logo_path)
        logo_html = (
            f"<img src='{data_uri}' alt='CSUSB logo' class='csusb-logo'/>"
            if data_uri else ""
        )

        st.markdown(
            f"""
            <div class="csusb-hero">
              <div class="csusb-hero-left">{logo_html}</div>
              <div class="csusb-hero-text">
                <h2>Welcome to Scholar AI Assistant</h2>
                <p>Your CSUSB-powered research companion for finding academic resources.</p>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Helpful note if logo not found so you can fix quickly.
        if not data_uri:
            with st.expander("Logo not found – quick fix", expanded=False):
                st.write("I tried these places and names. You can:")
                st.markdown("- Set **CSUSB_LOGO_PATH** env var to your image file")
                st.markdown("- Put a file like `CSU_San_Bernardino_seal.png` into `ui/assets/`")
                st.code(
                    f"Working dir: {os.getcwd()}\n"
                    f"Looked for names: {', '.join(CANDIDATE_NAMES)}\n"
                    f"Extensions: {', '.join(CANDIDATE_EXTS)}\n"
                    f"Folders: {', '.join(CANDIDATE_DIRS)}",
                    language="text",
                )

        st.divider()

    def handle_sidebar_actions(self):
        """Handle sidebar interactions."""
        new_search = render_sidebar()
        if new_search:
            reset_session_state()
            st.rerun()

        action = st.session_state.get("sidebar_action")
        if action in ("apply", "clear"):
            st.session_state.pop("sidebar_action", None)
            st.rerun()

    def display_initial_greeting(self):
        """Display initial greeting if no messages exist."""
        if len(st.session_state.messages) == 0:
            initial_message = get_initial_greeting()
            st.session_state.messages.append({"role": "assistant", "content": initial_message})
            with st.chat_message("assistant", avatar=get_assistant_avatar()):
                st.markdown(initial_message)

    def handle_chat_input(self):
        """Handle user chat input."""
        if prompt := st.chat_input("Enter your research query..."):
            handle_user_message(prompt, self.groq_client)

    def run(self):
        """Run the main application loop."""
        if not self.setup():
            return

        self.render_header()
        self.handle_sidebar_actions()
        render_chat_messages()
        display_search_results_section()
        self.display_initial_greeting()
        self.handle_chat_input()

# Application entry point
def main():
    app = ScholarAIApp()
    app.run()

# Entry point
if __name__ == "__main__":
    main()
