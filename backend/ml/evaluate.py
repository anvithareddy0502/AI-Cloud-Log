"""
Bridge for CLI: python -m backend.ml.evaluate
"""
from backend.app.ml.evaluate import main

if __name__ == "__main__":
    import sys
    sys.exit(main())
