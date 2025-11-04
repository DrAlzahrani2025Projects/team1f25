#!/usr/bin/env python
"""
Modern test runner using pytest.
Supports running unit tests, integration tests, or all tests.
"""
import sys
import subprocess
from pathlib import Path

# Get project root (parent of scripts directory)
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
TESTS_DIR = PROJECT_ROOT / "tests"

# Main function
def main():
    """Run tests based on command line arguments."""
    if len(sys.argv) < 2:
        print_usage()
        return
    
    test_type = sys.argv[1].lower()
    
    # Build pytest command (use python -m pytest for Windows compatibility)
    cmd = [sys.executable, "-m", "pytest"]
    
    if test_type == "unit":
        cmd.extend([str(TESTS_DIR / "unit"), "-m", "unit or not integration"])
        print("=" * 80)
        print("Running UNIT TESTS (no external dependencies)")
        print("=" * 80)
    
    elif test_type == "integration":
        cmd.extend([str(TESTS_DIR / "integration"), "-m", "integration"])
        print("=" * 80)
        print("Running INTEGRATION TESTS (requires network/APIs)")
        print("=" * 80)
    
    elif test_type == "e2e":
        cmd.extend([str(TESTS_DIR / "integration"), "-m", "e2e"])
        print("=" * 80)
        print("Running END-TO-END TESTS (complete workflows)")
        print("=" * 80)
    
    elif test_type == "all":
        cmd.append(str(TESTS_DIR))
        print("=" * 80)
        print("Running ALL TESTS")
        print("=" * 80)
    
    elif test_type == "legacy":
        print("=" * 80)
        print("Running LEGACY TESTS (old test scripts)")
        print("=" * 80)
        run_legacy_tests()
        return
    
    elif test_type == "--help" or test_type == "-h":
        print_usage()
        return
    
    else:
        print(f"Unknown test type: {test_type}")
        print_usage()
        return
    
    # Add verbose output
    cmd.extend(["-v", "--tb=short"])
    
    # Run pytest from project root
    try:
        result = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
        sys.exit(result.returncode)
    except FileNotFoundError:
        print("\n❌ Error: pytest not found!")
        print("Install it with: pip install pytest pytest-mock")
        sys.exit(1)

# Function to run legacy test scripts
def run_legacy_tests():
    """Run legacy test scripts for backward compatibility."""
    legacy_dir = TESTS_DIR
    legacy_scripts = [
        "check_types.py",
        "test_api_filter.py",
        "test_search.py",
        "test_filtering.py",
        "test_journal.py"
    ]
    
    passed = 0
    failed = 0
    
    for script in legacy_scripts:
        script_path = legacy_dir / script
        if script_path.exists():
            print(f"\n{'=' * 80}")
            print(f"Running: {script}")
            print("=" * 80)
            
            try:
                result = subprocess.run([sys.executable, str(script_path)])
                if result.returncode == 0:
                    print(f"[PASS] {script}")
                    passed += 1
                else:
                    print(f"[FAIL] {script}")
                    failed += 1
            except Exception as e:
                print(f"[ERROR] {script}: {e}")
                failed += 1
    
    print(f"\n{'=' * 80}")
    print(f"Legacy Tests: {passed} passed, {failed} failed")
    print("=" * 80)

# Function to print usage information
def print_usage():
    """Print usage information."""
    print("""
Modern Test Runner with pytest

Usage:
    python scripts/run_pytest.py <test_type>

Test Types:
    unit         - Run unit tests only (fast, no external dependencies)
    integration  - Run integration tests (requires network/APIs)
    e2e          - Run end-to-end workflow tests
    all          - Run all pytest tests
    legacy       - Run old test scripts (backward compatibility)
    
Options:
    -h, --help   - Show this help message

Examples:
    python scripts/run_pytest.py unit              # Run only unit tests
    python scripts/run_pytest.py integration       # Run integration tests
    python scripts/run_pytest.py all               # Run all pytest tests
    python scripts/run_pytest.py legacy            # Run legacy scripts

Additional pytest options:
    pytest tests/unit -v                   # Verbose unit tests
    pytest tests/integration -k "search"   # Run integration tests matching "search"
    pytest tests -m "not integration"      # Skip integration tests
    pytest tests --lf                      # Run last failed tests
    
Requirements:
    pip install pytest pytest-mock
""")

# Entry point
if __name__ == "__main__":
    main()
