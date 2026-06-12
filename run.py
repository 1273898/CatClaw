#!/usr/bin/env python3
"""PrivateClaw startup script - run directly without installation."""

import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Main entry point."""
    # Check Python version
    if sys.version_info < (3, 11):
        print("Error: Python 3.11 or higher is required.")
        print(f"Current version: {sys.version}")
        sys.exit(1)

    # Import and run
    try:
        from privateclaw.cli import main as cli_main
        cli_main()
    except ImportError as e:
        print(f"Import error: {e}")
        print("\nPlease install dependencies first:")
        print("  pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
