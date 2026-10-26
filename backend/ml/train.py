"""
Bridge for CLI: python -m backend.ml.train
"""
from backend.app.ml.train import main

if __name__ == "__main__":
    import sys
    sys.exit(main())
