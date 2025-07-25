#!/usr/bin/env python3
"""
Main entry point for RAG_07 application.
Handles only application startup and delegates to CLI module.
"""

if __name__ == '__main__':
    import sys
    from pathlib import Path

    # Add src to Python path for imports
    src_path = Path(__file__).parent
    sys.path.insert(0, str(src_path))

    # Import after path setup
    import cli

    cli.main()
