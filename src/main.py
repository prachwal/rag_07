"""
Main entry point for RAG_07 application.
Handles only application startup and delegates to CLI module.
"""

import sys
from pathlib import Path

# Add src to Python path for imports
src_path = Path(__file__).parent
sys.path.insert(0, str(src_path))

# Import after path setup
from src.cli import main  # type: ignore # noqa: E402

if __name__ == '__main__':
    main()
