#!/usr/bin/env python3
"""Convenience wrapper: run from repo root without -m flag.

Usage:
    python3 bin/analyze_learning.py
    python3 bin/analyze_learning.py --json
    python3 bin/analyze_learning.py --since 2026-04-20
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from framework.learning_analytics import main
raise SystemExit(main())
