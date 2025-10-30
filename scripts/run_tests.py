#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test Runner - Run all or specific tests

Usage:
    python scripts/run_tests.py              # Run all tests
    python scripts/run_tests.py search       # Run search-related tests
    python scripts/run_tests.py params       # Run parameter tests
    python scripts/run_tests.py e2e          # Run end-to-end tests
"""
# Standard Library Imports
import sys
import os
import subprocess
from pathlib import Path

# Get project root (parent of scripts directory)
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
TESTS_DIR = PROJECT_ROOT / "tests"

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Test categories
TEST_CATEGORIES = {
    "params": [
        "test_params.py",
        "test_journal_vs_article.py",
    ],
    "search": [
        "test_search.py",
        "test_api_filter.py",
        "test_filtering.py",
        "test_journal.py",
        "check_types.py",
    ],
    "e2e": [
        "test_e2e.py",
        "test_user_query.py",
        "test_comprehensive.py",
    ],
    "error": [
        "test_no_results.py",
        "test_suggestions.py",
        "test_conversation_flow.py",
    ],
}

def run_test(test_file):
    """Run a single test file."""
    print(f"\n{'='*80}")
    print(f"Running: {test_file}")
    print('='*80)
    
    test_path = TESTS_DIR / test_file
    if not test_path.exists():
        print(f"[FAIL] Test file not found: {test_path}")
        return False
    
    # Set UTF-8 environment for subprocess
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    
    result = subprocess.run([sys.executable, str(test_path)], env=env, cwd=str(PROJECT_ROOT))
    
    if result.returncode == 0:
        print(f"[PASS] {test_file} passed")
        return True
    else:
        print(f"[FAIL] {test_file} failed")
        return False

def run_category(category):
    """Run all tests in a category."""
    if category not in TEST_CATEGORIES:
        print(f"❌ Unknown category: {category}")
        print(f"Available categories: {', '.join(TEST_CATEGORIES.keys())}")
        return
    
    print(f"\n{'='*80}")
    print(f"Running {category.upper()} tests")
    print('='*80)
    
    tests = TEST_CATEGORIES[category]
    passed = 0
    failed = 0
    
    for test in tests:
        if run_test(test):
            passed += 1
        else:
            failed += 1
    
    print(f"\n{'='*80}")
    print(f"Results: {passed} passed, {failed} failed")
    print('='*80)
#beginning of code
def run_all_tests():
    """Run all tests."""
    print("\n" + "="*80)
    print("Running ALL tests")
    print("="*80)
    
    all_tests = set()
    for tests in TEST_CATEGORIES.values():
        all_tests.update(tests)
    
    passed = 0
    failed = 0
    
    for test in sorted(all_tests):
        if run_test(test):
            passed += 1
        else:
            failed += 1
    
    print(f"\n{'='*80}")
    print(f"FINAL Results: {passed} passed, {failed} failed")
    print('='*80)
#end of code
def main():
    if len(sys.argv) > 1:
        category = sys.argv[1].lower()
        
        if category == "all":
            run_all_tests()
        elif category in TEST_CATEGORIES:
            run_category(category)
        else:
            print(f"Usage: python scripts/run_tests.py [category]")
            print(f"\nAvailable categories:")
            for cat, tests in TEST_CATEGORIES.items():
                print(f"  {cat}: {len(tests)} tests")
            print(f"  all: Run all tests")
    else:
        print("Available test categories:")
        for cat, tests in TEST_CATEGORIES.items():
            print(f"\n{cat.upper()}:")
            for test in tests:
                print(f"  - {test}")
        print("\nUsage:")
        print("  python scripts/run_tests.py [category]")
        print("  python scripts/run_tests.py all")

if __name__ == "__main__":
    main()
