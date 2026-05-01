"""pytest config for xindex-mcp."""
from __future__ import annotations

import sys
from pathlib import Path

# Make `import server` resolve to docker/xindex-mcp/app/server.py
_APP = Path(__file__).resolve().parent.parent
if str(_APP) not in sys.path:
    sys.path.insert(0, str(_APP))
