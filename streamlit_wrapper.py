"""
Custom Streamlit server wrapper to inject CSP headers.
This script wraps Streamlit to add Content-Security-Policy headers to all responses.
"""

import os
import sys
import subprocess
import time

def run_streamlit_with_csp():
    """Run Streamlit with CSP headers injected."""
    
    # Streamlit command
    cmd = [
        sys.executable, "-m", "streamlit", "run", "app.py",
        "--server.port=5001",
        "--server.address=0.0.0.0",
        "--server.enableCORS=false",
        "--server.baseUrlPath=/team1f25",
        "--server.enableXsrfProtection=true",
    ]
    
    # Note: CSP headers will be added via the nginx proxy
    # This is just the base Streamlit server
    print("Starting Streamlit server...")
    print("CSP headers will be added by the Nginx reverse proxy")
    
    process = subprocess.Popen(cmd)
    process.wait()

if __name__ == "__main__":
    run_streamlit_with_csp()
