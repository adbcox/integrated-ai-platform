# Retired — anythingllm

**Retired:** 2026-05-01 (Phase 17 deliverable 17.F PARK-RETIRE)
**Audit:** [docs/audits/capability/anythingllm-2026-05-01.md](../../../docs/audits/capability/anythingllm-2026-05-01.md)
**Pattern:** PARK-RETIRE (compose parked, volumes preserved)

---

## Why retired

D#20 probe on 2026-05-01:
- 0 documents indexed
- 0 chat activity
- 3 workspaces present, all stub-named
- Service running ~25h with no meaningful net I/O

The RAG-over-docs capability is covered functionally by:
- **xindex** — repo / code knowledge
- **docs/external/articles/** — external write-ups
- **open-webui** — chat-style ad-hoc Q&A

~347 MiB RAM recovered.

---

## Volumes preserved

```
docker_anythingllm-storage   ← compose-namespaced; this is the active one
anythingllm-storage          ← legacy unnamespaced; also preserved
```

Both left in place by `docker compose rm -f anythingllm` (no `-v` flag).
Verify: `docker volume ls | grep anythingllm`.

---

## Restoration recipe

```bash
# 1. Move the parked compose back into docker/
git mv docker/_retired/anythingllm/docker-compose.parked.yml \
       docker/knowledge-stack.yml

# 2. Edit the file: remove the "PARKED" header block, keep the rest.

# 3. Bring the container back (volumes auto-remount)
cd docker && docker compose -f knowledge-stack.yml up -d anythingllm

# 4. Verify
docker ps | grep anythingllm
curl -sf http://localhost:3004/api/ping
```

If the legacy unnamespaced volume is preferred, swap the compose
volume reference from `anythingllm-storage:` to point at the
unnamespaced one. Otherwise the compose-namespaced
`docker_anythingllm-storage` is what gets remounted by default.

---

## What lives in the volume

- `lancedb` embedding store (path `/app/server/storage/lancedb/`)
- workspace metadata
- jwt secret + auth state

These survive retirement. Restoration recovers everything that was
in the running instance at retirement time (which was: 3 empty
workspaces, no documents, no chat — but the substrate is intact).
