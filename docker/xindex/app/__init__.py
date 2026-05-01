"""xindex — repo-local cross-index service (D-16-02).

Indexes ADRs, the Decision Register, and runbooks from the mounted /docs tree
into a SQLite + FTS5 database, and exposes query endpoints via FastAPI.
External sources (NetBox, Plane, Vault, InvenTree) are deferred to D-16-02.1/.2/.3.
"""

__version__ = "0.1.0"
