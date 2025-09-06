#!/usr/bin/env python3
"""Thin wrapper to keep 'py main.py' working. Delegates to src/main.py."""
from src.main import main

if __name__ == "__main__":
    main()
