#!/usr/bin/env python3
"""Trusted external pattern intake for Codex51 learning.

Downloads a bounded, approved upstream source set and extracts small reusable
patterns with attribution/license metadata for learning/code-library ingestion.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from collections import Counter, defaultdict
from datetime import datetime
from _datetime_compat import UTC
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = REPO_ROOT / "config" / "trusted_pattern_sources.json"
DEFAULT_OUT_DIR = REPO_ROOT / "artifacts" / "codex51" / "external_patterns"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(row, ensure_ascii=False) for row in rows]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def _run(args: list[str], *, cwd: Path | None = None) -> str:
    return subprocess.check_output(args, cwd=cwd, text=True, stderr=subprocess.STDOUT).strip()


def _safe_read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def _detect_license(repo_dir: Path) -> tuple[str, str]:
    for rel in ["LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING", "COPYING.md"]:
        p = repo_dir / rel
        if p.exists() and p.is_file():
            text = _safe_read(p)
            return rel, " ".join(text.split())[:1200]
    return "", ""


def _sync_repo(source: dict[str, Any], sources_dir: Path) -> dict[str, Any]:
    name = str(source.get("source_name") or "unknown")
    upstream_url = str(source.get("upstream_url") or "")
    preferred_ref = str(source.get("preferred_ref") or "main")
    ref_type = str(source.get("ref_type") or "branch")
    include_paths = [str(x) for x in (source.get("include_paths") or []) if str(x).strip()]
    include_paths.extend(["LICENSE*", "COPYING*", "README*", "pyproject.toml", "setup.cfg"])
    include_paths = sorted(set(include_paths))

    repo_dir = sources_dir / _slug(name)
    if not repo_dir.exists():
        _run(["git", "clone", "--depth", "1", "--filter=blob:none", "--sparse", upstream_url, str(repo_dir)])
    else:
        _run(["git", "-C", str(repo_dir), "remote", "set-url", "origin", upstream_url])

    if include_paths:
        _run(["git", "-C", str(repo_dir), "sparse-checkout", "set", "--no-cone", *include_paths])

    if ref_type == "tag":
        _run(["git", "-C", str(repo_dir), "fetch", "--depth", "1", "origin", f"refs/tags/{preferred_ref}"])
        _run(["git", "-C", str(repo_dir), "checkout", "--detach", "FETCH_HEAD"])
    elif ref_type == "commit":
        _run(["git", "-C", str(repo_dir), "fetch", "--depth", "1", "origin", preferred_ref])
        _run(["git", "-C", str(repo_dir), "checkout", "--detach", preferred_ref])
    else:
        _run(["git", "-C", str(repo_dir), "fetch", "--depth", "1", "origin", preferred_ref])
        _run(["git", "-C", str(repo_dir), "checkout", "--detach", "FETCH_HEAD"])

    commit = _run(["git", "-C", str(repo_dir), "rev-parse", "HEAD"])
    subject = _run(["git", "-C", str(repo_dir), "show", "-s", "--format=%s", "HEAD"])
    committed_at = _run(["git", "-C", str(repo_dir), "show", "-s", "--format=%cI", "HEAD"])
    license_path, license_text = _detect_license(repo_dir)

    return {
        "source_name": name,
        "upstream_repo": source.get("upstream_repo"),
        "upstream_url": upstream_url,
        "ref_type": ref_type,
        "requested_ref": preferred_ref,
        "resolved_commit": commit,
        "resolved_subject": subject,
        "resolved_committed_at": committed_at,
        "local_repo_dir": str(repo_dir),
        "license_path": license_path,
        "license_excerpt": license_text,
    }


def _infer_language(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".py", ".pyi"}:
        return "python"
    if suffix in {".sh", ".bash"}:
        return "shell"
    if suffix in {".go"}:
        return "go"
    if suffix in {".rs"}:
        return "rust"
    if suffix in {".toml"}:
        return "toml"
    if suffix in {".ini", ".cfg"}:
        return "ini"
    if suffix in {".md", ".rst"}:
        return "docs"
    if suffix in {".yaml", ".yml"}:
        return "yaml"
    return "text"


def _complexity_level(line_count: int, pattern_type: str) -> str:
    score = 0
    if pattern_type in {"helper", "module", "multi_file_pattern"}:
        score += 1
    if line_count > 18:
        score += 1
    if line_count > 60:
        score += 1
    if score <= 1:
        return "low"
    if score == 2:
        return "medium"
    return "high"


def _extract_python_patterns(content: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    lines = content.splitlines()
    for idx, line in enumerate(lines):
        m = re.match(r"^(def|class)\s+([A-Za-z_][A-Za-z0-9_]*)", line)
        if not m:
            continue
        start = idx
        end = min(len(lines), idx + 20)
        snippet = "\n".join(lines[start:end]).strip()
        if not snippet:
            continue
        ptype = "helper" if m.group(1) == "def" else "module"
        out.append(
            {
                "name": m.group(2),
                "pattern_type": ptype,
                "snippet": snippet[:3000],
                "line_count": max(1, end - start),
                "dependencies": sorted({
                    im.group(1)
                    for im in [re.match(r"^\s*from\s+([A-Za-z0-9_.]+)\s+import\s+", ln) for ln in lines[:80]]
                    if im
                }),
            }
        )
    fixture_lines = [ln for ln in lines if "@pytest.fixture" in ln]
    if fixture_lines:
        out.append(
            {
                "name": "pytest_fixture_template",
                "pattern_type": "template",
                "snippet": "\n".join((fixture_lines + lines[:12])[:18])[:3000],
                "line_count": min(18, len(fixture_lines) + 12),
                "dependencies": ["pytest"],
            }
        )
    test_defs = [ln for ln in lines if re.search(r"\bdef\s+test_[A-Za-z0-9_]+", ln)]
    if test_defs:
        out.append(
            {
                "name": "pytest_test_template",
                "pattern_type": "template",
                "snippet": "\n".join((test_defs + lines[:12])[:18])[:3000],
                "line_count": min(18, len(test_defs) + 12),
                "dependencies": ["pytest"],
            }
        )
    return out


def _extract_shell_patterns(content: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    lines = content.splitlines()
    for idx, line in enumerate(lines):
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\(\)\s*\{", line.strip())
        if not m:
            continue
        start = idx
        end = min(len(lines), idx + 24)
        out.append(
            {
                "name": m.group(1),
                "pattern_type": "helper",
                "snippet": "\n".join(lines[start:end])[:3000],
                "line_count": max(1, end - start),
                "dependencies": [],
            }
        )

    anti_tokens = {
        "eval ": "avoid eval in shell control paths",
        "`": "avoid backtick command substitution; prefer $(...)",
        "IFS=": "avoid global IFS mutations unless tightly scoped",
        "set +e": "avoid disabling shell strict mode in safety-critical scripts",
    }
    for idx, line in enumerate(lines):
        text = line.strip()
        for tok, reason in anti_tokens.items():
            if tok in text:
                out.append(
                    {
                        "name": f"shell_anti_pattern_{idx+1}",
                        "pattern_type": "snippet",
                        "snippet": text[:500],
                        "line_count": 1,
                        "dependencies": [],
                        "known_bad": [reason],
                        "direct_reuse_allowed": False,
                    }
                )
                break
    return out


def _extract_docs_patterns(content: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for code in re.findall(r"```(?:[a-zA-Z0-9_+-]+)?\n(.*?)```", content, re.DOTALL):
        snippet = "\n".join(code.strip().splitlines()[:18]).strip()
        if not snippet:
            continue
        out.append(
            {
                "name": "doc_code_template",
                "pattern_type": "template",
                "snippet": snippet[:3000],
                "line_count": len(snippet.splitlines()),
                "dependencies": [],
            }
        )
        if len(out) >= 4:
            break
    return out


def _extract_patterns_for_file(path: Path, source_name: str) -> list[dict[str, Any]]:
    content = _safe_read(path)
    if not content:
        return []
    lang = _infer_language(path)
    if lang == "python":
        rows = _extract_python_patterns(content)
    elif lang == "shell":
        rows = _extract_shell_patterns(content)
    elif lang == "docs":
        rows = _extract_docs_patterns(content)
    else:
        rows = []

    if not rows and lang in {"toml", "ini", "yaml"}:
        snippet = "\n".join(content.splitlines()[:24]).strip()
        if snippet:
            rows = [
                {
                    "name": f"{lang}_config_template",
                    "pattern_type": "template",
                    "snippet": snippet[:3000],
                    "line_count": len(snippet.splitlines()),
                    "dependencies": [],
                }
            ]

    for row in rows:
        row["language"] = lang
        row["family"] = source_name
    return rows


def _extract_source_patterns(source: dict[str, Any], sync_meta: dict[str, Any], *, max_patterns: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    repo_dir = Path(sync_meta["local_repo_dir"])
    globs = [str(x) for x in (source.get("extract_globs") or []) if str(x).strip()]
    task_class_hints = [str(x) for x in (source.get("task_class_hints") or [])]

    selected_files: list[Path] = []
    seen: set[str] = set()
    for pattern in globs:
        for p in sorted(repo_dir.glob(pattern)):
            if not p.is_file():
                continue
            rel = str(p.relative_to(repo_dir))
            if rel in seen:
                continue
            seen.add(rel)
            selected_files.append(p)
            if len(selected_files) >= 120:
                break
        if len(selected_files) >= 120:
            break

    patterns: list[dict[str, Any]] = []
    per_type: Counter[str] = Counter()
    for path in selected_files:
        rel = str(path.relative_to(repo_dir))
        for raw in _extract_patterns_for_file(path, str(source.get("source_name") or "external")):
            ptype = str(raw.get("pattern_type") or "snippet")
            line_count = int(raw.get("line_count") or max(1, len(str(raw.get("snippet") or "").splitlines())))
            snippet = str(raw.get("snippet") or "")
            direct_allowed = bool(raw.get("direct_reuse_allowed", True))
            known_bad = [str(x) for x in (raw.get("known_bad") or [])]
            confidence = 0.45
            if ptype in {"helper", "template"}:
                confidence += 0.2
            if len(task_class_hints) >= 2:
                confidence += 0.1
            if source.get("source_name") in {"shellcheck", "mvdan_sh"} and known_bad:
                confidence += 0.15
            if "test" in rel.lower() and source.get("source_name") == "pytest":
                confidence += 0.1
            confidence = max(0.05, min(0.99, confidence))

            row = {
                "schema_version": "trusted_external_pattern_v1",
                "trusted_external_reference": True,
                "source_name": str(source.get("source_name") or ""),
                "source_repo": str(source.get("upstream_repo") or ""),
                "source_url": str(source.get("upstream_url") or ""),
                "source_revision": str(sync_meta.get("resolved_commit") or ""),
                "source_ref": str(sync_meta.get("requested_ref") or ""),
                "source_path": rel,
                "license": str(source.get("license") or "unknown"),
                "license_path": str(sync_meta.get("license_path") or ""),
                "language": str(raw.get("language") or _infer_language(path)),
                "family": str(raw.get("family") or source.get("source_name") or "external"),
                "pattern_type": ptype,
                "complexity_level": _complexity_level(line_count, ptype),
                "intended_use": str(source.get("intended_use") or ""),
                "dependencies": [str(x) for x in (raw.get("dependencies") or [])][:8],
                "reuse_confidence": round(confidence, 3),
                "known_good_use_cases": task_class_hints,
                "known_bad_use_cases": known_bad,
                "direct_reuse_allowed": direct_allowed,
                "adaptation_required": True,
                "allowed_pattern_types": source.get("allowed_pattern_types") or [],
                "disallowed_direct_reuse_cases": source.get("disallowed_direct_reuse_cases") or [],
                "task_class_hints": task_class_hints,
                "name": str(raw.get("name") or "pattern"),
                "snippet": snippet[:3000],
                "line_count": line_count,
            }
            patterns.append(row)
            per_type[ptype] += 1
            if len(patterns) >= max_patterns:
                break
        if len(patterns) >= max_patterns:
            break

    # add one bounded multi-file pattern from top prefixes
    if patterns:
        prefixes = Counter(p["source_path"].split("/")[0] for p in patterns if "/" in p["source_path"])
        top_prefixes = [prefix for prefix, _ in prefixes.most_common(3)]
        if len(top_prefixes) >= 2:
            patterns.append(
                {
                    "schema_version": "trusted_external_pattern_v1",
                    "trusted_external_reference": True,
                    "source_name": str(source.get("source_name") or ""),
                    "source_repo": str(source.get("upstream_repo") or ""),
                    "source_url": str(source.get("upstream_url") or ""),
                    "source_revision": str(sync_meta.get("resolved_commit") or ""),
                    "source_ref": str(sync_meta.get("requested_ref") or ""),
                    "source_path": "<multi_file_pattern>",
                    "license": str(source.get("license") or "unknown"),
                    "license_path": str(sync_meta.get("license_path") or ""),
                    "language": ",".join(sorted({p["language"] for p in patterns[:10]})),
                    "family": str(source.get("source_name") or "external"),
                    "pattern_type": "multi_file_pattern",
                    "complexity_level": "medium",
                    "intended_use": str(source.get("intended_use") or ""),
                    "dependencies": top_prefixes,
                    "reuse_confidence": 0.61,
                    "known_good_use_cases": task_class_hints,
                    "known_bad_use_cases": [],
                    "direct_reuse_allowed": True,
                    "adaptation_required": True,
                    "allowed_pattern_types": source.get("allowed_pattern_types") or [],
                    "disallowed_direct_reuse_cases": source.get("disallowed_direct_reuse_cases") or [],
                    "task_class_hints": task_class_hints,
                    "name": "multi_file_reference_pattern",
                    "snippet": " | ".join(top_prefixes),
                    "line_count": len(top_prefixes),
                }
            )
            per_type["multi_file_pattern"] += 1

    summary = {
        "source_name": str(source.get("source_name") or ""),
        "selected_file_count": len(selected_files),
        "pattern_count": len(patterns),
        "pattern_type_counts": dict(per_type),
    }
    return patterns, summary


def _build_best_practice_priors(patterns: list[dict[str, Any]]) -> dict[str, Any]:
    buckets = {
        "python_helper_patterns": ["ruff", "pydantic"],
        "testing_patterns": ["pytest"],
        "shell_safety_patterns": ["shellcheck", "mvdan_sh"],
        "typed_schema_patterns": ["pydantic"],
        "browser_operator_patterns": ["playwright_python"],
    }

    out: dict[str, Any] = {
        "schema_version": "trusted_best_practice_priors_v1",
        "generated_at_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "families": {},
    }

    for name, source_names in buckets.items():
        rows = [p for p in patterns if str(p.get("source_name") or "") in source_names]
        rows.sort(key=lambda p: float(p.get("reuse_confidence") or 0.0), reverse=True)
        preferred = [
            {
                "source_name": p.get("source_name"),
                "pattern_type": p.get("pattern_type"),
                "name": p.get("name"),
                "source_path": p.get("source_path"),
                "reuse_confidence": p.get("reuse_confidence"),
                "task_class_hints": p.get("task_class_hints") or [],
            }
            for p in rows
            if bool(p.get("direct_reuse_allowed", True))
        ][:12]
        avoid = [
            {
                "source_name": p.get("source_name"),
                "name": p.get("name"),
                "source_path": p.get("source_path"),
                "reason": (p.get("known_bad_use_cases") or ["anti_pattern"])[0],
            }
            for p in rows
            if not bool(p.get("direct_reuse_allowed", True)) or (p.get("known_bad_use_cases") or [])
        ][:12]
        complexity = Counter(str(p.get("complexity_level") or "medium") for p in rows).most_common(1)
        out["families"][name] = {
            "preferred_patterns": preferred,
            "known_bad_patterns": avoid,
            "recommended_complexity": complexity[0][0] if complexity else "medium",
            "source_names": source_names,
        }

    return out


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Trusted external pattern intake for Codex51 learning.")
    parser.add_argument("--registry", default=str(DEFAULT_REGISTRY))
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    parser.add_argument("--max-patterns-per-source", type=int, default=48)
    parser.add_argument("--json-only", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    registry_path = Path(args.registry).resolve()
    out_dir = Path(args.out_dir).resolve()

    if not registry_path.exists():
        print(f"missing registry: {registry_path}")
        return 2

    registry = _read_json(registry_path)
    sources = registry.get("sources") if isinstance(registry.get("sources"), list) else []
    if not sources:
        print("registry has no sources")
        return 2

    approved = {
        "ruff",
        "pytest",
        "shellcheck",
        "mvdan_sh",
        "playwright_python",
        "pydantic",
    }

    bad = [str(row.get("source_name") or "") for row in sources if str(row.get("source_name") or "") not in approved]
    if bad:
        print(f"registry contains unapproved sources: {', '.join(sorted(set(bad)))}")
        return 2

    out_dir.mkdir(parents=True, exist_ok=True)
    sources_dir = out_dir / "sources"
    sources_dir.mkdir(parents=True, exist_ok=True)

    sync_rows: list[dict[str, Any]] = []
    patterns: list[dict[str, Any]] = []
    extraction_summaries: list[dict[str, Any]] = []

    for source in sources:
        sync_meta = _sync_repo(source, sources_dir)
        sync_rows.append(sync_meta)
        rows, summary = _extract_source_patterns(
            source,
            sync_meta,
            max_patterns=max(8, args.max_patterns_per_source),
        )
        patterns.extend(rows)
        extraction_summaries.append(summary)

    priors = _build_best_practice_priors(patterns)

    latest = {
        "schema_version": "trusted_external_intake_v1",
        "generated_at_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "registry_path": str(registry_path),
        "approved_sources": [str(row.get("source_name") or "") for row in sources],
        "sync": sync_rows,
        "extraction_summary": extraction_summaries,
        "pattern_count": len(patterns),
        "pattern_type_counts": dict(Counter(str(p.get("pattern_type") or "snippet") for p in patterns)),
        "license_map": {
            str(row.get("source_name") or ""): {
                "declared_license": next((s.get("license") for s in sources if s.get("source_name") == row.get("source_name")), ""),
                "license_path": row.get("license_path"),
            }
            for row in sync_rows
        },
    }

    _write_json(out_dir / "latest.json", latest)
    _write_jsonl(out_dir / "patterns.jsonl", patterns)
    _write_json(out_dir / "best_practice_priors.json", priors)

    if args.json_only:
        print(json.dumps(latest, ensure_ascii=False, indent=2))
    else:
        print("# Trusted External Pattern Intake")
        print(f"- generated_at_utc: {latest['generated_at_utc']}")
        print(f"- approved_sources: {', '.join(latest['approved_sources'])}")
        print(f"- pattern_count: {latest['pattern_count']}")
        for row in extraction_summaries:
            print(
                f"- {row['source_name']}: files={row['selected_file_count']} patterns={row['pattern_count']}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
