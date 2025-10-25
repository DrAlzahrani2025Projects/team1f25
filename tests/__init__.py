"""
Test configuration and utilities.
Add parent directory to path so tests can import from core/ and ui/ modules.
"""
import sys
from pathlib import Path

# Add parent directory to Python path
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))
