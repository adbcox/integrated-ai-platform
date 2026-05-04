# Hand-grade packet 03 — T2 long-context lc-finding-CC-prior-art

**Run:** 20260503T170223Z
**Model:** qwen2.5-coder:14b on mac-mini
**Workload:** long-context
**Task ID:** lc-finding-CC-prior-art

## Auto-grader output

- score: **1.0**
- pass: **True**
- notes: 5/5 expected facts present
- wall_s: 180.71079641699998, tps: 16.304857456867545

## Task summary

Recall the three prior-art patterns named in Finding CC

## Model response (full)

```
The three prior-art approaches for service registry / DNS resolution mentioned in Finding CC are:

1. **CoreDNS proxy on host forwarding to `127.0.0.11`** — exposes container DNS to host shell tools.
2. **`devdns` / `dockerdns` purpose-built tools watching Docker events maintaining DNS records.**
3. **Custom compose-aware inventory script producing canonical JSON of container → port mappings → credentials → dependencies for AI consultation.**
```

## Operator scoring

- [ ] coherent? (yes / no)
- [ ] addresses task? (yes / partial / no)
- [ ] ship-ready quality? (yes / no)
- [ ] auto-grade fair? (yes / too-low / too-high) — by how much?
- [ ] hand-grade 0.00-1.00: ___
- [ ] notes:
