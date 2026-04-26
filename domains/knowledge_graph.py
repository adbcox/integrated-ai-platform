"""domains/knowledge_graph.py — Roadmap item similarity, deduplication, and clustering.

Builds a semantic knowledge graph over roadmap items using Ollama embeddings
(with TF-IDF cosine similarity as a graceful fallback). Supports duplicate
detection, related item finding, cluster analysis, and cross-reference export.
"""

from __future__ import annotations

import hashlib
import json
import logging
import math
import os
import re
import random
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional dependencies
# ---------------------------------------------------------------------------
try:
    import requests  # type: ignore
    _REQUESTS_AVAILABLE = True
except ImportError:
    requests = None  # type: ignore[assignment]
    _REQUESTS_AVAILABLE = False
    logger.debug("requests not available — Ollama embeddings disabled")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
ITEMS_DEFAULT_DIR: str = "docs/roadmap/ITEMS"
ARTIFACTS_DIR: str = "artifacts"
EMBEDDINGS_CACHE_FILE: str = os.path.join(ARTIFACTS_DIR, "embeddings_cache.json")
GRAPH_JSON_FILE: str = os.path.join(ARTIFACTS_DIR, "knowledge_graph.json")
OLLAMA_EMBED_PATH: str = "/api/embeddings"
DEFAULT_EMBED_MODEL: str = "nomic-embed-text"
REQUEST_TIMEOUT: int = 30
DUPLICATE_THRESHOLD: float = 0.85
MIN_RELATED_SCORE: float = 0.65
DEFAULT_CLUSTERS: int = 10
KMEANS_MAX_ITER: int = 100
KMEANS_RANDOM_SEED: int = 42
SPARSE_CATEGORY_THRESHOLD: int = 3  # fewer than this → "sparse"


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------
@dataclass
class ItemNode:
    """A roadmap item with its semantic embedding.

    Attributes:
        id: RM-CATEGORY-NNN identifier.
        title: Short title string.
        description: Full description text (may be empty).
        category: Category slug.
        embedding: Float vector (empty until build_graph() is called).
    """

    id: str
    title: str
    description: str = ""
    category: str = ""
    embedding: List[float] = field(default_factory=list)


@dataclass
class SimilarityEdge:
    """A weighted similarity link between two roadmap items.

    Attributes:
        source_id: RM-ID of the source item.
        target_id: RM-ID of the target item.
        score: Cosine similarity in range [0, 1].
        reason: Short human-readable explanation of similarity.
    """

    source_id: str
    target_id: str
    score: float
    reason: str


# ---------------------------------------------------------------------------
# Knowledge graph
# ---------------------------------------------------------------------------
class KnowledgeGraph:
    """Build and query a semantic similarity graph over roadmap items.

    Example::

        kg = KnowledgeGraph()
        kg.load_items()
        kg.build_graph()
        dupes = kg.find_duplicates(threshold=0.85)
        clusters = kg.get_clusters(n_clusters=8)
    """

    def __init__(
        self,
        items_dir: str = ITEMS_DEFAULT_DIR,
        ollama_host: str = "localhost:11434",
    ) -> None:
        """Initialise the knowledge graph.

        Args:
            items_dir: Path to RM-*.md items directory.
            ollama_host: Host:port for the Ollama API server.
        """
        self.items_dir = items_dir
        self.ollama_host = ollama_host
        self._items: Dict[str, ItemNode] = {}
        self._embed_cache: Dict[str, List[float]] = {}
        self._ollama_available: Optional[bool] = None
        self._load_embed_cache()
        logger.info("KnowledgeGraph initialised (items_dir=%s, ollama=%s)", items_dir, ollama_host)

    # ------------------------------------------------------------------
    # Embedding cache
    # ------------------------------------------------------------------

    def _cache_key(self, text: str) -> str:
        """Compute a stable SHA-256 cache key for a text string.

        Args:
            text: Input text.

        Returns:
            Hex digest string.
        """
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def _load_embed_cache(self) -> None:
        """Load the on-disk embedding cache from artifacts/embeddings_cache.json."""
        if not os.path.exists(EMBEDDINGS_CACHE_FILE):
            return
        try:
            with open(EMBEDDINGS_CACHE_FILE, "r") as fh:
                self._embed_cache = json.load(fh)
            logger.info("_load_embed_cache: %d cached embeddings", len(self._embed_cache))
        except Exception as exc:
            logger.warning("_load_embed_cache: %s", exc)

    def _save_embed_cache(self) -> None:
        """Persist the in-memory embedding cache to disk."""
        try:
            os.makedirs(ARTIFACTS_DIR, exist_ok=True)
            with open(EMBEDDINGS_CACHE_FILE, "w") as fh:
                json.dump(self._embed_cache, fh)
        except Exception as exc:
            logger.warning("_save_embed_cache: %s", exc)

    # ------------------------------------------------------------------
    # Ollama
    # ------------------------------------------------------------------

    def _check_ollama(self) -> bool:
        """Return True if Ollama is reachable (cached after first probe).

        Returns:
            True if Ollama API responds to a health check.
        """
        if self._ollama_available is not None:
            return self._ollama_available
        if not _REQUESTS_AVAILABLE:
            self._ollama_available = False
            return False
        try:
            resp = requests.get(f"http://{self.ollama_host}/api/tags", timeout=3)
            self._ollama_available = resp.status_code == 200
        except Exception:
            self._ollama_available = False
        logger.info("Ollama available: %s", self._ollama_available)
        return self._ollama_available

    def get_embedding(self, text: str, model: str = DEFAULT_EMBED_MODEL) -> List[float]:
        """Return the embedding vector for a text string.

        Checks the disk cache first, then calls Ollama /api/embeddings.
        Falls back to an empty list if Ollama is unavailable.

        Args:
            text: Input text.
            model: Embedding model name (default 'nomic-embed-text').

        Returns:
            List of floats (embedding vector), or empty list.
        """
        key = self._cache_key(text)
        if key in self._embed_cache:
            return self._embed_cache[key]

        if not self._check_ollama():
            return []

        try:
            resp = requests.post(  # type: ignore[union-attr]
                f"http://{self.ollama_host}{OLLAMA_EMBED_PATH}",
                json={"model": model, "prompt": text},
                timeout=REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
            embedding: List[float] = resp.json()["embedding"]
            self._embed_cache[key] = embedding
            return embedding
        except Exception as exc:
            logger.warning("get_embedding: %s", exc)
            self._ollama_available = False
            return []

    # ------------------------------------------------------------------
    # Items loading
    # ------------------------------------------------------------------

    def _parse_md(self, path: Path) -> Optional[ItemNode]:
        """Parse a RM-*.md file and return an ItemNode.

        Args:
            path: Path to the markdown file.

        Returns:
            ItemNode or None on failure.
        """
        item_id = path.stem
        if not re.match(r"^RM-[A-Z]+-\d+$", item_id):
            return None
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            logger.warning("_parse_md: %s — %s", path, exc)
            return None

        title = item_id
        for line in text.splitlines():
            if line.startswith("#"):
                title = line.lstrip("#").strip()
                break

        # Strip markdown headers/links for description
        clean = re.sub(r"#+ .*", "", text)
        clean = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", clean)
        description = " ".join(clean.split())[:1_000]  # cap at 1000 chars

        category = item_id.split("-")[1] if "-" in item_id else ""
        return ItemNode(id=item_id, title=title, description=description, category=category)

    def load_items(self) -> List[ItemNode]:
        """Load all RM-*.md items from the items directory.

        Returns:
            List of ItemNode objects.
        """
        self._items.clear()
        items_path = Path(self.items_dir)
        if not items_path.exists():
            logger.warning("load_items: items_dir '%s' does not exist", self.items_dir)
            return []

        for md_file in sorted(items_path.glob("RM-*.md")):
            node = self._parse_md(md_file)
            if node:
                self._items[node.id] = node

        logger.info("load_items: loaded %d items", len(self._items))
        return list(self._items.values())

    # ------------------------------------------------------------------
    # Graph building
    # ------------------------------------------------------------------

    def _item_text(self, node: ItemNode) -> str:
        """Concatenate item fields into a single text for embedding.

        Args:
            node: ItemNode to represent.

        Returns:
            Combined text string.
        """
        return f"{node.title} {node.category} {node.description}"

    def build_graph(self, batch_size: int = 10) -> None:
        """Generate embeddings for all items and build the similarity matrix.

        Items are processed in batches. Uses Ollama when available; falls back
        to TF-IDF vectors. Persists the embedding cache after completion.

        Args:
            batch_size: Number of items to embed per batch (for logging progress).
        """
        if not self._items:
            self.load_items()

        items = list(self._items.values())
        use_ollama = self._check_ollama()
        logger.info("build_graph: embedding %d items (ollama=%s)", len(items), use_ollama)

        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            for node in batch:
                text = self._item_text(node)
                if use_ollama:
                    emb = self.get_embedding(text)
                    if emb:
                        node.embedding = emb
                    else:
                        node.embedding = self._tfidf_vector(text, items)
                else:
                    node.embedding = self._tfidf_vector(text, items)
                self._items[node.id] = node
            logger.info("build_graph: embedded %d/%d", min(i + batch_size, len(items)), len(items))

        self._save_embed_cache()

        # Write graph JSON
        try:
            os.makedirs(ARTIFACTS_DIR, exist_ok=True)
            with open(GRAPH_JSON_FILE, "w") as fh:
                json.dump(self.to_graph_json(), fh, indent=2)
            logger.info("build_graph: graph written to %s", GRAPH_JSON_FILE)
        except Exception as exc:
            logger.warning("build_graph: could not write graph — %s", exc)

    # ------------------------------------------------------------------
    # TF-IDF fallback
    # ------------------------------------------------------------------

    def _tokenize(self, text: str) -> List[str]:
        """Simple whitespace/punctuation tokenizer.

        Args:
            text: Input text.

        Returns:
            List of lowercase tokens.
        """
        return re.findall(r"[a-z0-9]+", text.lower())

    def _tfidf_vector(self, text: str, corpus: List[ItemNode]) -> List[float]:
        """Compute a TF-IDF vector for text against the corpus.

        Uses stdlib Counter for term frequencies and log-IDF weighting.

        Args:
            text: Text to vectorise.
            corpus: All items (for IDF calculation).

        Returns:
            Sparse TF-IDF vector as a list of floats (vocabulary-aligned).
        """
        # Build vocabulary from corpus
        all_texts = [self._item_text(n) for n in corpus]
        vocab: Dict[str, int] = {}
        for t in all_texts:
            for tok in self._tokenize(t):
                if tok not in vocab:
                    vocab[tok] = len(vocab)

        n_docs = max(len(all_texts), 1)
        # DF: number of documents containing each term
        df: Dict[str, int] = Counter()
        for t in all_texts:
            toks = set(self._tokenize(t))
            for tok in toks:
                df[tok] += 1

        tokens = self._tokenize(text)
        tf = Counter(tokens)
        total_terms = max(len(tokens), 1)

        vector = [0.0] * len(vocab)
        for tok, idx in vocab.items():
            if tf[tok] > 0:
                tf_val = tf[tok] / total_terms
                idf_val = math.log((n_docs + 1) / (df.get(tok, 0) + 1)) + 1
                vector[idx] = tf_val * idf_val

        return vector

    # ------------------------------------------------------------------
    # Similarity utilities
    # ------------------------------------------------------------------

    def _cosine(self, a: List[float], b: List[float]) -> float:
        """Cosine similarity between two vectors.

        Args:
            a: First vector.
            b: Second vector.

        Returns:
            Similarity in [-1, 1], or 0.0 on dimension mismatch or zero norms.
        """
        if not a or not b or len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a))
        nb = math.sqrt(sum(y * y for y in b))
        if na == 0.0 or nb == 0.0:
            return 0.0
        return dot / (na * nb)

    # ------------------------------------------------------------------
    # Public graph queries
    # ------------------------------------------------------------------

    def find_duplicates(self, threshold: float = DUPLICATE_THRESHOLD) -> List[SimilarityEdge]:
        """Find item pairs with similarity above the duplicate threshold.

        Args:
            threshold: Minimum cosine similarity to flag as duplicate.

        Returns:
            List of SimilarityEdge objects sorted by score descending.
        """
        items = list(self._items.values())
        dupes: List[SimilarityEdge] = []
        seen: Set[Tuple[str, str]] = set()

        for i, a in enumerate(items):
            for j, b in enumerate(items):
                if i >= j:
                    continue
                pair = (a.id, b.id)
                if pair in seen:
                    continue
                seen.add(pair)

                score = self._cosine(a.embedding, b.embedding)
                if score >= threshold:
                    dupes.append(SimilarityEdge(
                        source_id=a.id,
                        target_id=b.id,
                        score=round(score, 4),
                        reason=f"High semantic similarity ({score:.2%}) — potential duplicate",
                    ))

        dupes.sort(key=lambda e: e.score, reverse=True)
        logger.info("find_duplicates(threshold=%.2f): %d duplicate pairs", threshold, len(dupes))
        return dupes

    def find_related(
        self,
        item_id: str,
        top_n: int = 5,
        min_score: float = MIN_RELATED_SCORE,
    ) -> List[SimilarityEdge]:
        """Find the most similar items to a given item.

        Args:
            item_id: Reference item ID.
            top_n: Maximum number of related items to return.
            min_score: Minimum similarity score to include.

        Returns:
            List of SimilarityEdge objects sorted by score descending.
        """
        if item_id not in self._items:
            logger.warning("find_related: item_id '%s' not found", item_id)
            return []

        ref = self._items[item_id]
        edges: List[SimilarityEdge] = []

        for other_id, other in self._items.items():
            if other_id == item_id:
                continue
            score = self._cosine(ref.embedding, other.embedding)
            if score >= min_score:
                edges.append(SimilarityEdge(
                    source_id=item_id,
                    target_id=other_id,
                    score=round(score, 4),
                    reason=f"Semantic similarity {score:.2%}",
                ))

        edges.sort(key=lambda e: e.score, reverse=True)
        return edges[:top_n]

    def suggest_cross_references(self, item_id: str) -> List[str]:
        """Generate 'see also' cross-reference suggestions for an item.

        Args:
            item_id: Reference item ID.

        Returns:
            List of formatted strings like 'see also RM-ML-042'.
        """
        related = self.find_related(item_id, top_n=5, min_score=MIN_RELATED_SCORE)
        return [f"see also {edge.target_id}" for edge in related]

    # ------------------------------------------------------------------
    # K-means clustering (stdlib only)
    # ------------------------------------------------------------------

    def get_clusters(self, n_clusters: int = DEFAULT_CLUSTERS) -> Dict[int, List[str]]:
        """Cluster items by embedding similarity using k-means.

        Implements a simple k-means from scratch (no sklearn dependency).
        Falls back to category-based clustering if embeddings are unavailable.

        Args:
            n_clusters: Number of clusters to produce.

        Returns:
            Dict mapping cluster_id → list of item_ids.
        """
        items = [n for n in self._items.values() if n.embedding]
        if not items:
            logger.warning("get_clusters: no embeddings available, falling back to category clustering")
            return self._category_clusters(n_clusters)

        n = min(n_clusters, len(items))
        if n == 0:
            return {}

        rng = random.Random(KMEANS_RANDOM_SEED)
        # Initialise centroids by sampling n random items
        centroids = [list(items[i].embedding) for i in rng.sample(range(len(items)), n)]
        assignments = [-1] * len(items)

        for iteration in range(KMEANS_MAX_ITER):
            new_assignments = []
            for item in items:
                best_cluster = 0
                best_score = -2.0
                for k, centroid in enumerate(centroids):
                    score = self._cosine(item.embedding, centroid)
                    if score > best_score:
                        best_score = score
                        best_cluster = k
                new_assignments.append(best_cluster)

            # Check convergence
            if new_assignments == assignments:
                logger.info("get_clusters: converged after %d iterations", iteration + 1)
                break
            assignments = new_assignments

            # Update centroids
            dim = len(centroids[0])
            for k in range(n):
                members = [items[i].embedding for i, a in enumerate(assignments) if a == k]
                if members:
                    centroids[k] = [
                        sum(v[d] for v in members) / len(members)
                        for d in range(dim)
                    ]

        result: Dict[int, List[str]] = {k: [] for k in range(n)}
        for i, item in enumerate(items):
            result[assignments[i]].append(item.id)

        return result

    def _category_clusters(self, n_clusters: int) -> Dict[int, List[str]]:
        """Fallback clustering: group items by category.

        Args:
            n_clusters: Maximum number of clusters (extra categories merged).

        Returns:
            Dict mapping cluster_id → list of item_ids.
        """
        by_cat: Dict[str, List[str]] = {}
        for node in self._items.values():
            by_cat.setdefault(node.category, []).append(node.id)
        result: Dict[int, List[str]] = {}
        for i, (_, ids) in enumerate(by_cat.items()):
            if i >= n_clusters:
                result[n_clusters - 1].extend(ids)
            else:
                result[i] = ids
        return result

    # ------------------------------------------------------------------
    # Gap analysis
    # ------------------------------------------------------------------

    def find_gaps(self, categories: Optional[List[str]] = None) -> List[str]:
        """Identify categories with sparse item coverage.

        Args:
            categories: List of expected category slugs. If None, all known
                categories are examined.

        Returns:
            List of category slugs that have fewer than SPARSE_CATEGORY_THRESHOLD items.
        """
        cat_counts: Dict[str, int] = Counter(n.category for n in self._items.values())
        if categories is None:
            categories = list(cat_counts.keys())

        sparse = [
            cat for cat in categories
            if cat_counts.get(cat, 0) < SPARSE_CATEGORY_THRESHOLD
        ]
        logger.info("find_gaps: %d sparse categories (threshold=%d)", len(sparse), SPARSE_CATEGORY_THRESHOLD)
        return sparse

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def to_graph_json(self) -> dict:
        """Export the graph as D3-compatible JSON with similarity edges.

        Returns:
            Dict with 'nodes' and 'links' keys for D3.js force graph.
        """
        nodes = [
            {
                "id": node.id,
                "title": node.title,
                "category": node.category,
                "has_embedding": bool(node.embedding),
            }
            for node in self._items.values()
        ]

        # Build similarity links (score >= min_related)
        items = list(self._items.values())
        seen: Set[Tuple[str, str]] = set()
        links: List[dict] = []

        for i, a in enumerate(items):
            for j, b in enumerate(items):
                if i >= j or not a.embedding or not b.embedding:
                    continue
                score = self._cosine(a.embedding, b.embedding)
                if score >= MIN_RELATED_SCORE:
                    pair = tuple(sorted([a.id, b.id]))
                    if pair not in seen:
                        seen.add(pair)  # type: ignore[arg-type]
                        links.append({
                            "source": a.id,
                            "target": b.id,
                            "value": round(score, 4),
                        })

        return {"nodes": nodes, "links": links}

    def export_cross_references(self) -> str:
        """Export a markdown document of cross-reference suggestions for all items.

        Returns:
            Markdown string with item_id → see-also suggestions.
        """
        lines = ["# Knowledge Graph Cross-References\n"]
        for item_id in sorted(self._items):
            refs = self.suggest_cross_references(item_id)
            if refs:
                lines.append(f"## {item_id}")
                for ref in refs:
                    lines.append(f"- {ref}")
                lines.append("")
        return "\n".join(lines)
