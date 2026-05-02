# Capability Audit — anythingllm

**Date:** 2026-05-01
**Auditor:** Claude session (operator decision: PARK-RETIRE)
**Trigger:** 17.F agent UI consolidation audit. anythingllm was
flagged as a possible retirement candidate based on minimal observed
usage.

---

## Section 1 — Tool identification

- **Name:** anythingllm (AnythingLLM by Mintplex Labs)
- **Container:** `anythingllm`, image
  `mintplexlabs/anythingllm:latest` (floating tag — separate hygiene
  issue, but moot under retirement).
- **Compose location:** in-repo at `docker/knowledge-stack.yml`
  (anythingllm block at line 21–48; volume `anythingllm-storage` at
  line 58 of that file).
- **Resource cost (live, 2026-05-01):** 346.9 MiB RAM (1.45% of
  23.42 GiB limit), 0.00% CPU, 34 PIDs, 243 MB read I/O. Restart
  count 0, uptime ~25h.

---

## Section 2 — Probed capabilities

- **Stated purpose:** "all-in-one AI productivity accelerator" — a
  RAG-over-uploaded-docs UI with workspaces, embeddings, chat.
- **Configured stack:** `VECTOR_DB=lancedb`,
  `EMBEDDING_ENGINE=ollama`. Local-first, no cloud dependency.
- **Probe — actual usage (D#20):**
  - **0 documents** indexed across the instance.
  - **3 workspaces** present, all stub-named:
    `engineering-25568046`, `roadmap-items`, `test-ingestion`.
  - **0 chat activity** — no message history beyond probing.
  - Net I/O: 362 kB rx / 9.88 kB tx in stats sample — service is
    running, but receiving and emitting essentially nothing.
- **Conclusion:** the tool is provisioned but has never been
  populated with content or used for the workflow it was deployed
  to support.

---

## Section 3 — Stack-coverage analysis

| Function                          | Provided by               |
|-----------------------------------|---------------------------|
| RAG over docs (intended)          | anythingllm (this — unused) |
| Repo-aware code search            | xindex + xindex-mcp       |
| Operator chat over LLM            | open-webui                |
| Article-intake structured records | docs/external/articles/   |

The intended capability (RAG over uploaded docs) overlaps
philosophically with xindex (repo-knowledge), articles store
(external knowledge), and open-webui (chat). With the platform
having converged on those substrates instead, anythingllm sits
between them with **no current consumer**.

---

## Section 4 — Verdict: **PARK-RETIRE**

**Rationale:**
1. Zero documents, zero chat — the tool has not earned the
   ~347 MiB RAM cost.
2. The capability gap it would fill (RAG over uploaded docs) is
   covered functionally by xindex (code), the articles store
   (external write-ups), and open-webui chat for ad-hoc Q&A.
3. PARK (not full DELETE) keeps the door open to reactivation if
   the operator later builds a content corpus that warrants a
   dedicated RAG UI.
4. **Volume preservation is required** — `anythingllm-storage` may
   contain the lancedb embedding index, even if empty workspaces
   suggest it's small. Park, do not destroy.

**Operator confirmed retirement (2026-05-01).**

---

## Section 5 — Migration / retirement plan

**Pattern:** PARK-RETIRE per established platform doctrine
(matches 17.E zabbix-exporter bridge, 17.H sportarr).

**Steps:**

1. **Stop the container:**
   ```bash
   docker compose -f docker/knowledge-stack.yml stop anythingllm
   docker compose -f docker/knowledge-stack.yml rm -f anythingllm
   ```

2. **Park the compose block:** move the anythingllm service block
   (and the `anythingllm-storage` volume declaration) from
   `docker/knowledge-stack.yml` into a new file
   `docker/_retired/anythingllm/docker-compose.parked.yml`.
   - Comment the file header with retirement date, reason, and
     restoration recipe.
   - Keep the volume DECLARATION but do not remove the volume from
     Docker.

3. **Preserve the volume:** `docker volume ls | grep anythingllm` —
   leave the named volume in place. Document its name in the parked
   compose for future restoration.

4. **README:** add `docker/_retired/anythingllm/README.md` with:
   - Retirement date and rationale (zero documents, zero chat).
   - Volume name and recovery command.
   - Restoration recipe (move parked block back, `docker compose up`).
   - Reference to this audit doc.

5. **Caddy:** if `anythingllm.internal` is in `docker/caddy/Caddyfile`,
   prune the route. (Verify presence; this is an unblock-the-parity-
   check moment, not a separate concern.)

6. **Remove the row from any service-registry / topology data** that
   listed anythingllm as live.

**Restoration recipe (for the README):**

```bash
# 1. Move parked compose block back into knowledge-stack.yml
mv docker/_retired/anythingllm/docker-compose.parked.yml docker/knowledge-stack.yml.add
# (operator merges the block manually into knowledge-stack.yml)

# 2. Bring the container back
docker compose -f docker/knowledge-stack.yml up -d anythingllm

# 3. Volume is automatically remounted (it was preserved)
```

---

## Section 6 — Decision log

- **17.A stack-audit hypothesis:** "RAG-over-docs candidate;
  utilization unknown" — **CONFIRMED unused via D#20 probe (0 docs,
  0 chat).**
- **Operator decision (2026-05-01):** PARK-RETIRE.
- **Volume policy:** preserved; recovery is one `docker compose up`
  away if the operator builds a content corpus that warrants
  reactivation.
- **Resource recovery:** ~347 MiB RAM freed.
