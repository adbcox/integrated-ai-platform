# tests/capability

Reserved for narrow capability sessions tied to ratification evidence.

Only bounded, isolated tests that drive framework runtime primitives against
tmp-path workspaces belong here. No tactical-family tests (eo_*, ed_*, mc_*,
live_bridge_*, ort_*, pgs_*) are permitted in this directory. Tests here
must:

- operate entirely within `tmp_path` workspaces,
- never mutate repo files,
- never monkey-patch framework modules,
- carry no network dependency.

See `governance/authority_adr_0008_phase2_closure.md` for the current
capability session that authorized this directory.
