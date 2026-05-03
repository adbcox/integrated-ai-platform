"""D-17-31 — PHASE_ROADMAP.md scope-section parser.

Reads `docs/PHASE_ROADMAP.md` and emits one `RoadmapItem` per scope
bullet under each `### NN.X` sub-block heading. Sister to
`scripts/openproject-sync-from-framework.py`'s `parse_framework`, which
parses the §9 deliverable table.

Authoritative for: Phase 16 sub-blocks (16.A/B/C), Phase 18 sub-blocks
(18.A/B/C/D). Phase 17 is intentionally NOT parsed here — its scope
lives in `docs/phase-17/PHASE_17_PLAN_*.md` and the framework §9 table,
both of which the framework-sync already covers.

Scope-section shape:

    ### 16.A — Mac Studio full compute stack (~12–18h)

    Builds on Block D day-1.

    **Scope:**
    - Ollama on Studio: pull qwen2.5-coder:32b + llama3.3:70b ...
    - LiteLLM Gateway on Mini: add `studio-fast` ...
    ...

    **Gate:** ...

The parser:
  * Locates `### NN.X — title (effort)` headings under Phase 16 / 18.
  * Finds the `**Scope:**` marker in that section.
  * Captures every `- ` bullet until the next `**Bold:**` marker
    (Gate / ADR / Hard prerequisites / etc.) or the next `###`.
  * Multi-line bullets (continuation lines indented by two spaces)
    are joined with a single space.
  * Each bullet becomes one RoadmapItem.

ID scheme: `RM-<phase>-<sub>-<NNN>` zero-padded ordinal, e.g.
`RM-16-A-001`, `RM-18-D-001`. Chosen by D-17-31 WP-02 surface-back to
operator (approved 2026-05-03). Avoids collision with `D-NN-MM`
framework IDs and the existing `RM-*` autonomous-coding micro-task
corpus (whose prefixes are `RM-A11Y-*`, `RM-API-*`, etc., never
`RM-NN-X-*`).

18.D has no `**Scope:**` marker (paragraph form). The parser emits a
single synthetic item for it from the section heading + first paragraph.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


# ── Heuristic: autonomous-coding capability flag ─────────────────────────────

# Approved 2026-05-03 (D-17-31 WP-02 surface-back).
# Items whose scope text matches any of these markers get the
# `autonomous-coding` category. Items matching the NEGATIVE markers
# do NOT get the flag (planning/judgment work, not hardening).
AUTONOMOUS_CODING_POSITIVE = re.compile(
    r"\b("
    r"scripts?/|"           # scripts/oura-ingest.py, scripts/print-…
    r"services?\b|"
    r"routes?\b|"
    r"endpoints?\b|"
    r"dashboards?\b|"
    r"plugins?\b|"
    r"harness(?:es)?\b|"
    r"agents?\b|"
    r"MCP\b|"
    r"prompt librar(?:y|ies)|"
    r"provenance\b|"
    r"capabilit(?:y|ies)\b|"
    r"inference\b"
    r")",
    re.IGNORECASE,
)

# Negative markers — even if a positive marker matches, these veto.
# "Eval/review/audit/decision" = planning, not autonomous-codable build.
AUTONOMOUS_CODING_NEGATIVE = re.compile(
    r"\b("
    r"audit\b|"
    r"review\b|"
    r"evaluation\b|"
    r"\beval\b|"
    r"decision\b|"
    r"ADR-?[A-Z]?-?\d+\b"   # naming an ADR = decision artifact
    r")",
    re.IGNORECASE,
)


def is_autonomous_codable(scope_text: str) -> bool:
    if AUTONOMOUS_CODING_NEGATIVE.search(scope_text):
        return False
    return bool(AUTONOMOUS_CODING_POSITIVE.search(scope_text))


# ── Data model ───────────────────────────────────────────────────────────────

@dataclass
class RoadmapItem:
    phase: int                  # 16 or 18
    sub_block: str              # "A", "B", "C", "D"
    ordinal: int                # 1-indexed within the sub-block
    title: str                  # first-line summary of the bullet
    scope_text: str             # full bullet text (multi-line joined)
    autonomous_coding: bool

    @property
    def external_id(self) -> str:
        return f"RM-{self.phase}-{self.sub_block}-{self.ordinal:03d}"


@dataclass
class SubBlock:
    phase: int
    letter: str                 # "A".."D"
    heading: str                # full heading text e.g. "Mac Studio full compute stack (~12–18h)"
    items: list[RoadmapItem] = field(default_factory=list)


# ── Parsing ──────────────────────────────────────────────────────────────────

# `### 16.A — Mac Studio full compute stack (~12–18h)` or
# `### 18.D — Network flow collection + visualization (deferred from Phase 16)`
SUBBLOCK_RE = re.compile(
    r"^###\s+(?P<phase>16|18)\.(?P<letter>[A-D])\s+[—–-]\s+(?P<title>.+?)\s*$"
)
SCOPE_MARKER_RE = re.compile(r"^\*\*Scope:\*\*\s*$")
END_MARKER_RE = re.compile(r"^\*\*[^*]+:\*\*")            # **Gate:** **ADR-…:** etc.
BULLET_RE = re.compile(r"^-\s+(?P<text>.+?)\s*$")
CONT_RE = re.compile(r"^\s{2,}(?P<text>\S.*?)\s*$")


def parse_roadmap(md_path: Path) -> list[SubBlock]:
    text = md_path.read_text()
    lines = text.splitlines()

    sub_blocks: list[SubBlock] = []
    i = 0
    while i < len(lines):
        m = SUBBLOCK_RE.match(lines[i])
        if not m:
            i += 1
            continue
        phase = int(m.group("phase"))
        letter = m.group("letter")
        heading = m.group("title").strip()
        sb = SubBlock(phase=phase, letter=letter, heading=heading)

        # Walk forward to find **Scope:** or next ### heading.
        j = i + 1
        scope_at: int | None = None
        while j < len(lines):
            if SUBBLOCK_RE.match(lines[j]) or lines[j].startswith("## "):
                break
            if SCOPE_MARKER_RE.match(lines[j]):
                scope_at = j
                break
            j += 1

        if scope_at is None:
            # 18.D special case — no **Scope:**; synthesize one item from
            # the section paragraph (lines i+1 .. next ### or ##).
            paragraph_lines: list[str] = []
            k = i + 1
            while k < len(lines):
                if SUBBLOCK_RE.match(lines[k]) or lines[k].startswith("## "):
                    break
                if lines[k].strip():
                    paragraph_lines.append(lines[k].strip())
                k += 1
            paragraph = " ".join(paragraph_lines).strip()
            if paragraph:
                title = paragraph.split(". ", 1)[0].rstrip(".") + "."
                if len(title) > 120:
                    title = title[:117] + "…"
                sb.items.append(RoadmapItem(
                    phase=phase,
                    sub_block=letter,
                    ordinal=1,
                    title=title,
                    scope_text=paragraph,
                    autonomous_coding=is_autonomous_codable(paragraph),
                ))
            sub_blocks.append(sb)
            i = k
            continue

        # Walk bullets after **Scope:** until end marker or next ###.
        k = scope_at + 1
        ordinal = 1
        cur_bullet: list[str] | None = None

        def flush_bullet():
            nonlocal cur_bullet, ordinal
            if cur_bullet:
                joined = " ".join(cur_bullet).strip()
                title = joined.split(":", 1)[0] if ":" in joined and len(joined.split(":", 1)[0]) < 80 else joined
                if len(title) > 120:
                    title = title[:117] + "…"
                sb.items.append(RoadmapItem(
                    phase=phase,
                    sub_block=letter,
                    ordinal=ordinal,
                    title=title,
                    scope_text=joined,
                    autonomous_coding=is_autonomous_codable(joined),
                ))
                ordinal += 1
                cur_bullet = None

        while k < len(lines):
            line = lines[k]
            if SUBBLOCK_RE.match(line) or line.startswith("## "):
                flush_bullet()
                break
            if END_MARKER_RE.match(line):
                flush_bullet()
                # Skip past the end-marker block (read until blank or next ###)
                k += 1
                while k < len(lines) and lines[k].strip() and not SUBBLOCK_RE.match(lines[k]) and not lines[k].startswith("## "):
                    k += 1
                # Continue scanning — there may be more **Scope:**-equivalents,
                # but for our roadmap shape, **Gate:** is the terminator.
                # Walk forward to next ### or ##.
                while k < len(lines) and not SUBBLOCK_RE.match(lines[k]) and not lines[k].startswith("## "):
                    k += 1
                break

            bm = BULLET_RE.match(line)
            if bm:
                flush_bullet()
                cur_bullet = [bm.group("text")]
                k += 1
                continue

            cm = CONT_RE.match(line)
            if cm and cur_bullet is not None:
                cur_bullet.append(cm.group("text"))
                k += 1
                continue

            # Blank line inside scope — preserve, don't flush yet
            # (the next line might be a bullet continuation).
            if not line.strip():
                k += 1
                continue

            # Non-blank, non-bullet, non-cont — likely the start of a
            # narrative paragraph between bullets. Flush and continue.
            flush_bullet()
            k += 1

        flush_bullet()
        sub_blocks.append(sb)
        i = k

    return sub_blocks


# ── CLI for hand-running / debugging ─────────────────────────────────────────

def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Parse PHASE_ROADMAP.md scope sections")
    ap.add_argument("--path", default=None, help="Override roadmap path")
    ap.add_argument("--show-text", action="store_true", help="Print full scope_text per item")
    args = ap.parse_args()

    repo = Path(__file__).resolve().parents[2]
    md_path = Path(args.path) if args.path else repo / "docs" / "PHASE_ROADMAP.md"

    sub_blocks = parse_roadmap(md_path)
    total = sum(len(sb.items) for sb in sub_blocks)
    auto_count = sum(1 for sb in sub_blocks for it in sb.items if it.autonomous_coding)
    print(f"Parsed {len(sub_blocks)} sub-block(s), {total} item(s), {auto_count} autonomous-codable")
    print()
    for sb in sub_blocks:
        flag_count = sum(1 for it in sb.items if it.autonomous_coding)
        print(f"  Phase {sb.phase}.{sb.letter}: {len(sb.items)} item(s), {flag_count} auto-codable — {sb.heading}")
        for it in sb.items:
            mark = "★" if it.autonomous_coding else " "
            print(f"    {mark} {it.external_id}  {it.title[:90]}")
            if args.show_text:
                print(f"        {it.scope_text[:160]}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
