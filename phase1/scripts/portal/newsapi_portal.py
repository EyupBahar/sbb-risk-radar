"""Backward-compatibility shim — delegates to data_portal.py."""
from data_portal import main
import sys

if __name__ == "__main__":
    raise SystemExit(main())
