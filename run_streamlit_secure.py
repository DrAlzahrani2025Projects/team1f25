"""
Streamlit app launcher with security configuration.
"""
import subprocess
import sys
import os

if __name__ == "__main__":
    # Set Streamlit config
    os.environ['STREAMLIT_SERVER_PORT'] = '5001'
    os.environ['STREAMLIT_SERVER_ADDRESS'] = '0.0.0.0'
    os.environ['STREAMLIT_SERVER_ENABLE_CORS'] = 'false'
    os.environ['STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION'] = 'true'
    os.environ['STREAMLIT_SERVER_BASE_URL_PATH'] = '/team1f25'
    
    # Run Streamlit
    cmd = [
        sys.executable, "-m", "streamlit", "run", "app.py",
        "--server.port=5001",
        "--server.address=0.0.0.0",
        "--server.enableCORS=false",
        "--server.baseUrlPath=/team1f25",
        "--server.enableXsrfProtection=true",
    ]
    
    subprocess.run(cmd)

