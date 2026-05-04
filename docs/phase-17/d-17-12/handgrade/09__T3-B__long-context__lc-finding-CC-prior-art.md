# Hand-grade packet 09 — T3-B long-context lc-finding-CC-prior-art

**Run:** 20260503T180613Z
**Model:** qwen3-coder:30b on mac-studio
**Workload:** long-context
**Task ID:** lc-finding-CC-prior-art

## Auto-grader output

- score: **0.6**
- pass: **False**
- notes: 3/5 expected facts present
- wall_s: 46.699769833000005, tps: 45.29500853380793

## Task summary

Recall the three prior-art patterns named in Finding CC

## Model response (full)

```
Based on Document B, the three prior-art approaches for service registry / DNS resolution mentioned in Finding CC are:

1.  **Docker's embedded DNS:** The embedded DNS at `127.0.0.11` provides internal name → IP resolution for container-to-container traffic.
2.  **CoreDNS proxy:** A CoreDNS proxy on the host forwarding to `127.0.0.11`, exposing container DNS to host shell tools.
3.  **`devdns` / `dockerdns`:** Purpose-built tools watching Docker events and maintaining DNS records.
```

## Operator scoring

- [ ] coherent? (yes / no)
- [ ] addresses task? (yes / partial / no)
- [ ] ship-ready quality? (yes / no)
- [ ] auto-grade fair? (yes / too-low / too-high) — by how much?
- [ ] hand-grade 0.00-1.00: ___
- [ ] notes:
