#!/usr/bin/env python3
"""Task decomposer: breaks roadmap items into executable subtasks via LLM."""
from __future__ import annotations

import json
import logging
import os
import time
import urllib.request
import urllib.error
from typing import Dict, List, Optional

log = logging.getLogger(__name__)

_OLLAMA_URL = os.environ.get("OLLAMA_API_BASE", "http://127.0.0.1:11434")
_DEFAULT_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5-coder:14b")

_DECOMPOSE_PROMPT = """\
You are a senior software engineer decomposing a roadmap item into concrete, executable subtasks.

Roadmap item:
- ID: {item_id}
- Title: {title}
- Category: {category}
- Priority: {priority}
- Description: {description}

Break this into 3-7 concrete subtasks. Each subtask must be independently executable.
Return a JSON array with no other text. Each element:
{{
  "order": 1,
  "id": "subtask-1",
  "title": "Short action-oriented title",
  "description": "What exactly to implement/change",
  "target_files": ["path/to/file.py"],
  "estimated_minutes": 30,
  "test_command": "pytest tests/test_example.py",
  "depends_on": []
}}
JSON array only:"""

_PLAN_PROMPT = """\
You are a technical project manager creating an execution plan for a roadmap item.

Roadmap item:
- ID: {item_id}
- Title: {title}
- Category: {category}
- Priority: {priority}
- Description: {description}

Create a full execution plan. Return JSON only:
{{
  "item_id": "{item_id}",
  "title": "{title}",
  "estimated_total_minutes": 120,
  "risk_level": "low|medium|high",
  "approach": "Brief description of implementation approach",
  "subtasks": [
    {{
      "id": "subtask-1",
      "title": "Short title",
      "description": "What to do",
      "target_files": ["path/to/file.py"],
      "estimated_minutes": 30,
      "depends_on": []
    }}
  ],
  "validation_steps": [
    "make check",
    "python3 -m pytest tests/ -x"
  ],
  "notes": "Any important caveats or prerequisites"
}}
JSON only:"""


def _call_ollama(prompt: str, model: str = _DEFAULT_MODEL, timeout: int = 60) -> str:
    payload = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.2, "num_predict": 1024},
    }).encode()
    req = urllib.request.Request(
        f"{_OLLAMA_URL}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = json.loads(r.read())
    return data.get("response", "").strip()


def _extract_json(text: str, prefer_object: bool = False) -> object:
    """Extract first JSON array or object from LLM response."""
    text = text.strip()
    # Try direct parse — check { before [ when caller expects an object,
    # because a plan object like {"subtasks":[...]} contains [ internally.
    order = [("{", "}"), ("[", "]")] if prefer_object else [("[", "]"), ("{", "}")]
    for start_ch, end_ch in order:
        idx = text.find(start_ch)
        if idx == -1:
            continue
        # Find matching close
        depth = 0
        in_str = False
        escape = False
        for i, ch in enumerate(text[idx:], idx):
            if escape:
                escape = False
                continue
            if ch == "\\" and in_str:
                escape = True
                continue
            if ch == '"':
                in_str = not in_str
                continue
            if in_str:
                continue
            if ch == start_ch:
                depth += 1
            elif ch == end_ch:
                depth -= 1
                if depth == 0:
                    return json.loads(text[idx:i + 1])
    raise ValueError(f"No JSON found in: {text[:200]}")


class TaskDecomposer:
    """Decomposes roadmap items into executable subtasks using a local LLM."""

    def __init__(self, model: str = _DEFAULT_MODEL) -> None:
        self.model = model

    def _build_item_vars(self, roadmap_item: Dict) -> Dict[str, str]:
        return {
            "item_id":     roadmap_item.get("id", "UNKNOWN"),
            "title":       roadmap_item.get("title", "Untitled"),
            "category":    roadmap_item.get("category", "GENERAL"),
            "priority":    roadmap_item.get("priority", "medium"),
            "description": (roadmap_item.get("description", "") or "No description provided.")[:600],
        }

    def decompose(self, roadmap_item: Dict) -> List[Dict]:
        """Break a roadmap item into 3-7 executable subtasks.

        Returns list of subtask dicts. Falls back to a single generic subtask on error.
        """
        vars_ = self._build_item_vars(roadmap_item)
        prompt = _DECOMPOSE_PROMPT.format(**vars_)

        try:
            raw = _call_ollama(prompt, model=self.model)
            subtasks = _extract_json(raw)
            if not isinstance(subtasks, list):
                raise ValueError("Expected JSON array")
            # Normalise each subtask
            cleaned: List[Dict] = []
            for i, st in enumerate(subtasks):
                if not isinstance(st, dict):
                    continue
                cleaned.append({
                    "order":             int(st.get("order", i + 1)),
                    "id":                st.get("id", f"subtask-{i + 1}"),
                    "title":             st.get("title", f"Subtask {i + 1}"),
                    "description":       st.get("description", ""),
                    "target_files":      st.get("target_files", []),
                    "estimated_minutes": int(st.get("estimated_minutes", 30)),
                    "test_command":      st.get("test_command"),
                    "depends_on":        st.get("depends_on", []),
                })
            return cleaned or self._fallback_subtasks(vars_)
        except Exception as exc:
            log.warning("decompose LLM call failed (%s), using fallback", exc)
            return self._fallback_subtasks(vars_)

    def create_execution_plan(self, roadmap_item: Dict) -> Dict:
        """Return a full execution plan dict with subtasks and validation steps."""
        vars_ = self._build_item_vars(roadmap_item)
        prompt = _PLAN_PROMPT.format(**vars_)

        try:
            raw = _call_ollama(prompt, model=self.model, timeout=90)
            plan = _extract_json(raw, prefer_object=True)
            if not isinstance(plan, dict):
                raise ValueError("Expected JSON object")
            # Ensure required keys
            plan.setdefault("item_id",                vars_["item_id"])
            plan.setdefault("title",                  vars_["title"])
            plan.setdefault("estimated_total_minutes", 120)
            plan.setdefault("risk_level",              "medium")
            plan.setdefault("approach",                "")
            plan.setdefault("subtasks",                self._fallback_subtasks(vars_))
            plan.setdefault("validation_steps",        ["make check"])
            plan.setdefault("notes",                   "")
            return plan
        except Exception as exc:
            log.warning("create_execution_plan LLM call failed (%s), using fallback", exc)
            return {
                "item_id":                vars_["item_id"],
                "title":                  vars_["title"],
                "estimated_total_minutes": 60,
                "risk_level":             "medium",
                "approach":               "Manual implementation required — LLM unavailable",
                "subtasks":               self._fallback_subtasks(vars_),
                "validation_steps":       ["make check", "make quick"],
                "notes":                  f"LLM error: {exc}",
            }

    @staticmethod
    def _fallback_subtasks(vars_: Dict) -> List[Dict]:
        return [{
            "order":             1,
            "id":                "subtask-1",
            "title":             f"Implement {vars_['title']}",
            "description":       vars_["description"] or "See roadmap item for details.",
            "target_files":      [],
            "estimated_minutes": 60,
            "test_command":      None,
            "depends_on":        [],
        }]


# ── CLI convenience ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    sample = {
        "id":          sys.argv[1] if len(sys.argv) > 1 else "RM-DEV-001",
        "title":       sys.argv[2] if len(sys.argv) > 2 else "Add metrics endpoint",
        "category":    "DEV",
        "priority":    "medium",
        "description": "Expose a /metrics endpoint compatible with Prometheus scraping.",
    }

    td = TaskDecomposer()
    plan = td.create_execution_plan(sample)
    print(json.dumps(plan, indent=2))
