"""Simple loader for the test/mock_results.csv to verify pandas can read it.

Usage: python scripts/load_mock.py
"""
import os
import pandas as pd

CSV_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "test", "mock_results.csv")

def main():
    print(f"Loading CSV from: {CSV_PATH}")
    df = pd.read_csv(CSV_PATH)
    print("--- DataFrame head ---")
    print(df.head().to_string(index=False))
    print(f"\nRows: {df.shape[0]}, Columns: {df.shape[1]}")

if __name__ == '__main__':
    main()
