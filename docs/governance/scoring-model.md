# RGC Package Scoring Model

## Purpose

Each feature-block package receives a composite score in `[0.0, 1.0]` that reflects the relative delivery priority of its member roadmap items, adjusted for CMDB traceability and outstanding integrity issues.

Scores are used to order packages in `GET /packages` (highest score first) and are recorded in package artifacts for audit purposes.

## Formula

```
score = clamp(normalised + link_bonus - finding_penalty, 0.0, 1.0)
```

### Step 1 — Priority weight per item

| Priority | Weight |
|---|---|
| P0 | 4 |
| P1 | 3 |
| P2 | 2 |
| P3 | 1 |
| other | 1 |

### Step 2 — Raw score

```
raw = sum(weight(item) for item in package.members)
```

### Step 3 — Normalised score

```
max_possible = len(members) * 4
normalised = raw / max_possible        # range: [0.25, 1.0] for valid priorities
```

If a package has no members, `normalised = 0.0`.

### Step 4 — Link bonus

```
link_bonus = 0.10  if any member has a roadmap_link (CMDB link)
           = 0.00  otherwise
```

The bonus rewards packages where at least one item has been traced to a CMDB entity, indicating operational grounding.

### Step 5 — Finding penalty

```
finding_penalty = 0.05 × open_finding_count
```

Where `open_finding_count` = number of `IntegrityFinding` rows with `status="open"` and `object_ref` in the package's member set.

Each unresolved open finding reduces the score by 5 percentage points, capped at 0.0.

### Step 6 — Clamp

```
final_score = max(0.0, min(1.0, normalised + link_bonus - finding_penalty))
```

## Examples

**Example 1: Four P1 items, two CMDB-linked, no open findings**

```
raw = 4 × 3 = 12
normalised = 12 / 16 = 0.75
link_bonus = 0.10   (at least one linked)
finding_penalty = 0.0
score = 0.85
```

**Example 2: Two P0 items, no CMDB links, one open finding**

```
raw = 2 × 4 = 8
normalised = 8 / 8 = 1.0
link_bonus = 0.0
finding_penalty = 0.05
score = 0.95
```

**Example 3: One P3 item, no links, four open findings**

```
raw = 1
normalised = 1 / 4 = 0.25
link_bonus = 0.0
finding_penalty = 0.20
score = max(0.0, 0.05) = 0.05
```

## Rationale field

Each package also stores a human-readable rationale string:

```
{n} item(s); {linked} with CMDB links; {open_findings} open finding(s); score={score:.3f}
```

## Implementation

`roadmap_governance/planner_service.py::_score`
