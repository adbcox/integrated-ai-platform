"""domains/content_recommender.py — Plex-history-driven content recommendations.

Parses Plex watch history, generates vector embeddings via Ollama, and uses
cosine similarity to surface relevant new content from TMDB trending/similar
endpoints. Recommended items can be automatically added to Sonarr or Radarr.
"""

from __future__ import annotations

import logging
import math
from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

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
    logger.warning("requests not available — HTTP calls will fail gracefully")

try:
    from framework.event_bus import publish_event  # type: ignore
except ImportError:
    def publish_event(name: str, payload: dict) -> None:  # type: ignore[misc]
        logger.debug("event_bus unavailable — skipped event: %s", name)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
EMBEDDING_MODEL: str = "nomic-embed-text"
EMBEDDING_CACHE_MAX: int = 1_000
PLEX_HISTORY_PATH: str = "/status/sessions/history/all"
TMDB_BASE_URL: str = "https://api.themoviedb.org/3"
REQUEST_TIMEOUT: int = 15      # seconds
MIN_JACCARD_SCORE: float = 0.0  # include all when falling back to genre matching


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------
@dataclass
class ContentItem:
    """A show or movie with its key metadata.

    Attributes:
        id: Internal Plex or library ID string.
        title: Human-readable title.
        year: Release year.
        genres: List of genre strings.
        rating: Numeric rating (0–10).
        tmdb_id: TMDB identifier (0 if unknown).
        type: Either 'show' or 'movie'.
    """

    id: str
    title: str
    year: int
    genres: List[str]
    rating: float
    tmdb_id: int
    type: str  # "show" | "movie"


@dataclass
class Recommendation:
    """A single content recommendation.

    Attributes:
        item: The recommended ContentItem.
        score: Similarity or relevance score (0–1).
        reason: Human-readable explanation.
        source: Origin of the recommendation ('embedding', 'genre', 'trending').
    """

    item: ContentItem
    score: float
    reason: str
    source: str


# ---------------------------------------------------------------------------
# Recommender
# ---------------------------------------------------------------------------
class ContentRecommender:
    """Generate personalised content recommendations from watch history.

    Behaviour degrades gracefully: if Ollama is unavailable, Jaccard similarity
    over shared genres is used instead of embedding cosine similarity.

    Example::

        rec = ContentRecommender(plex_token="MY_TOKEN", tmdb_api_key="MY_KEY")
        history = rec.get_plex_history(limit=200)
        recs = rec.generate_recommendations(history=history, limit=10)
    """

    def __init__(
        self,
        plex_url: str = "",
        plex_token: str = "",
        tmdb_api_key: str = "",
        ollama_host: str = "localhost:11434",
    ) -> None:
        """Initialise the recommender with service credentials.

        Args:
            plex_url: Base URL for the Plex Media Server (e.g. 'http://localhost:32400').
            plex_token: Plex authentication token (X-Plex-Token).
            tmdb_api_key: TMDB v3 API key.
            ollama_host: Host:port for Ollama (default 'localhost:11434').
        """
        self.plex_url = plex_url.rstrip("/")
        self.plex_token = plex_token
        self.tmdb_api_key = tmdb_api_key
        self.ollama_host = ollama_host
        self._embedding_cache: Dict[str, List[float]] = {}
        self._ollama_available: Optional[bool] = None
        logger.info("ContentRecommender initialised (plex=%s, ollama=%s)", plex_url, ollama_host)

    # ------------------------------------------------------------------
    # Ollama availability
    # ------------------------------------------------------------------

    def _check_ollama(self) -> bool:
        """Return True if Ollama is reachable.

        Result is cached after the first successful or failed probe.

        Returns:
            True if Ollama API is reachable.
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

    # ------------------------------------------------------------------
    # Plex
    # ------------------------------------------------------------------

    def get_plex_history(self, limit: int = 500) -> List[ContentItem]:
        """Fetch watch history from Plex Media Server.

        Args:
            limit: Maximum number of history entries to retrieve.

        Returns:
            List of ContentItem objects from watch history.
        """
        if not _REQUESTS_AVAILABLE or not self.plex_url:
            logger.warning("get_plex_history: requests unavailable or plex_url not set")
            return []
        try:
            url = f"{self.plex_url}{PLEX_HISTORY_PATH}"
            params = {
                "X-Plex-Token": self.plex_token,
                "limit": limit,
            }
            resp = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            items: List[ContentItem] = []
            for entry in data.get("MediaContainer", {}).get("Metadata", []):
                items.append(ContentItem(
                    id=str(entry.get("ratingKey", "")),
                    title=entry.get("title", ""),
                    year=int(entry.get("year", 0)),
                    genres=[g["tag"] for g in entry.get("Genre", [])],
                    rating=float(entry.get("audienceRating", entry.get("rating", 0.0))),
                    tmdb_id=int(entry.get("tmdbId", 0)),
                    type="show" if entry.get("type") == "episode" else "movie",
                ))
            logger.info("get_plex_history: fetched %d items", len(items))
            return items
        except Exception as exc:
            logger.error("get_plex_history: %s", exc)
            return []

    # ------------------------------------------------------------------
    # Embeddings
    # ------------------------------------------------------------------

    def get_embedding(self, text: str) -> List[float]:
        """Generate or retrieve a cached embedding vector for the given text.

        Uses Ollama /api/embeddings. Falls back to an empty list if Ollama
        is unavailable; callers should check for empty list and switch to
        genre-based fallback.

        Args:
            text: Input text to embed.

        Returns:
            List of floats (embedding vector), or empty list on failure.
        """
        if text in self._embedding_cache:
            return self._embedding_cache[text]

        if not self._check_ollama():
            return []

        try:
            resp = requests.post(  # type: ignore[union-attr]
                f"http://{self.ollama_host}/api/embeddings",
                json={"model": EMBEDDING_MODEL, "prompt": text},
                timeout=REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
            embedding: List[float] = resp.json()["embedding"]

            # LRU eviction: remove oldest entry when cache is full
            if len(self._embedding_cache) >= EMBEDDING_CACHE_MAX:
                oldest_key = next(iter(self._embedding_cache))
                del self._embedding_cache[oldest_key]

            self._embedding_cache[text] = embedding
            return embedding
        except Exception as exc:
            logger.warning("get_embedding failed: %s", exc)
            self._ollama_available = False
            return []

    def cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Compute cosine similarity between two vectors.

        Args:
            a: First embedding vector.
            b: Second embedding vector.

        Returns:
            Cosine similarity in range [−1, 1], or 0.0 on dimension mismatch.
        """
        if not a or not b or len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(y * y for y in b))
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return dot / (norm_a * norm_b)

    def _jaccard_similarity(self, genres_a: List[str], genres_b: List[str]) -> float:
        """Compute Jaccard similarity between two genre lists.

        Args:
            genres_a: First item's genre list.
            genres_b: Second item's genre list.

        Returns:
            Jaccard similarity in range [0, 1].
        """
        set_a = set(g.lower() for g in genres_a)
        set_b = set(g.lower() for g in genres_b)
        if not set_a and not set_b:
            return 0.0
        intersection = len(set_a & set_b)
        union = len(set_a | set_b)
        return intersection / union if union > 0 else 0.0

    def _item_text(self, item: ContentItem) -> str:
        """Build a text representation of a ContentItem for embedding.

        Args:
            item: ContentItem to represent.

        Returns:
            Concatenated title, year, genres, and type string.
        """
        genres_str = ", ".join(item.genres)
        return f"{item.title} ({item.year}) {genres_str} {item.type}"

    # ------------------------------------------------------------------
    # Similarity search
    # ------------------------------------------------------------------

    def find_similar(
        self,
        item: ContentItem,
        candidates: List[ContentItem],
        top_n: int = 10,
    ) -> List[Recommendation]:
        """Find the most similar content items to a given item.

        Uses embedding cosine similarity if Ollama is available; falls back
        to Jaccard similarity on genres.

        Args:
            item: The reference ContentItem.
            candidates: Pool of items to score against.
            top_n: Maximum number of results to return.

        Returns:
            List of Recommendation objects sorted by score descending.
        """
        ref_embedding = self.get_embedding(self._item_text(item))
        use_embeddings = bool(ref_embedding)

        scored: List[Tuple[float, ContentItem, str]] = []
        for candidate in candidates:
            if candidate.id == item.id:
                continue
            if use_embeddings:
                cand_embedding = self.get_embedding(self._item_text(candidate))
                score = self.cosine_similarity(ref_embedding, cand_embedding) if cand_embedding else 0.0
                source = "embedding"
                reason = f"Embedding similarity {score:.2f} to '{item.title}'"
            else:
                score = self._jaccard_similarity(item.genres, candidate.genres)
                source = "genre"
                reason = f"Shares genres with '{item.title}'"
            scored.append((score, candidate, reason))

        scored.sort(key=lambda t: t[0], reverse=True)
        return [
            Recommendation(item=c, score=round(s, 4), reason=r, source=source)
            for s, c, r in scored[:top_n]
        ]

    # ------------------------------------------------------------------
    # TMDB
    # ------------------------------------------------------------------

    def _tmdb_get(self, path: str, params: dict = None) -> dict:
        """Make an authenticated TMDB API request.

        Args:
            path: URL path under TMDB_BASE_URL (without leading slash).
            params: Additional query parameters.

        Returns:
            JSON response dict, or empty dict on failure.
        """
        if not _REQUESTS_AVAILABLE or not self.tmdb_api_key:
            return {}
        try:
            all_params = {"api_key": self.tmdb_api_key}
            if params:
                all_params.update(params)
            resp = requests.get(f"{TMDB_BASE_URL}/{path}", params=all_params, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:
            logger.warning("_tmdb_get %s: %s", path, exc)
            return {}

    def _tmdb_results_to_items(self, results: List[dict], media_type: str = "movie") -> List[ContentItem]:
        """Convert raw TMDB result dicts to ContentItem objects.

        Args:
            results: List of TMDB API result dicts.
            media_type: 'movie' or 'tv'.

        Returns:
            List of ContentItem objects.
        """
        items: List[ContentItem] = []
        for r in results:
            item_type = "show" if (r.get("media_type", media_type) in ("tv", "show")) else "movie"
            title = r.get("title", r.get("name", ""))
            release = r.get("release_date", r.get("first_air_date", "0000"))
            year = int(release[:4]) if release and len(release) >= 4 else 0
            items.append(ContentItem(
                id=str(r.get("id", "")),
                title=title,
                year=year,
                genres=[],  # TMDB trending doesn't include genre names inline
                rating=float(r.get("vote_average", 0.0)),
                tmdb_id=int(r.get("id", 0)),
                type=item_type,
            ))
        return items

    def get_tmdb_trending(self, media_type: str = "all") -> List[ContentItem]:
        """Fetch TMDB weekly trending content.

        Args:
            media_type: 'all', 'movie', or 'tv'.

        Returns:
            List of trending ContentItems.
        """
        data = self._tmdb_get(f"trending/{media_type}/week")
        results = data.get("results", [])
        items = self._tmdb_results_to_items(results, media_type)
        logger.info("get_tmdb_trending(%s): %d items", media_type, len(items))
        return items

    def get_tmdb_similar(self, tmdb_id: int, media_type: str = "movie") -> List[ContentItem]:
        """Fetch content similar to a specific TMDB entry.

        Args:
            tmdb_id: TMDB identifier.
            media_type: 'movie' or 'tv'.

        Returns:
            List of similar ContentItems.
        """
        endpoint = "movie" if media_type == "movie" else "tv"
        data = self._tmdb_get(f"{endpoint}/{tmdb_id}/similar")
        results = data.get("results", [])
        items = self._tmdb_results_to_items(results, media_type)
        logger.info("get_tmdb_similar(%d, %s): %d items", tmdb_id, media_type, len(items))
        return items

    # ------------------------------------------------------------------
    # Recommendations
    # ------------------------------------------------------------------

    def generate_recommendations(
        self,
        history: Optional[List[ContentItem]] = None,
        limit: int = 20,
    ) -> List[Recommendation]:
        """Generate personalised recommendations from watch history.

        Combines TMDB trending with similarity scoring against the user's
        watch history. Falls back gracefully if Plex or Ollama are unavailable.

        Args:
            history: Pre-fetched watch history (fetched automatically if None).
            limit: Maximum number of recommendations to return.

        Returns:
            List of Recommendation objects sorted by score descending.
        """
        if history is None:
            history = self.get_plex_history()

        history_ids = {item.id for item in history}

        # Get candidate pool from TMDB trending
        candidates = self.get_tmdb_trending(media_type="all")
        # Also pull similar items for top-rated history entries
        top_history = sorted(history, key=lambda i: i.rating, reverse=True)[:5]
        for ref_item in top_history:
            if ref_item.tmdb_id:
                candidates += self.get_tmdb_similar(ref_item.tmdb_id, media_type=ref_item.type)

        # Deduplicate candidates and exclude already-watched items
        seen_ids: set = set()
        unique_candidates: List[ContentItem] = []
        for c in candidates:
            if c.id not in seen_ids and c.id not in history_ids:
                seen_ids.add(c.id)
                unique_candidates.append(c)

        if not unique_candidates:
            logger.warning("generate_recommendations: no candidate pool available")
            return []

        # Score against history items
        all_recommendations: Dict[str, Recommendation] = {}
        for history_item in top_history:
            recs = self.find_similar(history_item, unique_candidates, top_n=limit)
            for rec in recs:
                existing = all_recommendations.get(rec.item.id)
                if existing is None or rec.score > existing.score:
                    all_recommendations[rec.item.id] = rec

        sorted_recs = sorted(all_recommendations.values(), key=lambda r: r.score, reverse=True)
        final = sorted_recs[:limit]

        publish_event("media.recommendation.generated", {"count": len(final)})
        logger.info("generate_recommendations: %d recommendations generated", len(final))
        return final

    # ------------------------------------------------------------------
    # Auto-add
    # ------------------------------------------------------------------

    def auto_add_to_sonarr(self, rec: Recommendation, sonarr_url: str, api_key: str) -> bool:
        """Add a recommended show to Sonarr.

        Args:
            rec: Recommendation containing a ContentItem of type 'show'.
            sonarr_url: Base URL for the Sonarr instance.
            api_key: Sonarr API key.

        Returns:
            True if the series was successfully added.
        """
        if not _REQUESTS_AVAILABLE:
            logger.warning("auto_add_to_sonarr: requests unavailable")
            return False
        if rec.item.type != "show":
            logger.warning("auto_add_to_sonarr: item '%s' is not a show", rec.item.title)
            return False
        try:
            payload = {
                "title": rec.item.title,
                "year": rec.item.year,
                "tvdbId": 0,
                "tmdbId": rec.item.tmdb_id,
                "qualityProfileId": 1,
                "rootFolderPath": "/tv",
                "addOptions": {"searchForMissingEpisodes": True},
                "monitored": True,
            }
            resp = requests.post(
                f"{sonarr_url.rstrip('/')}/api/v3/series",
                json=payload,
                headers={"X-Api-Key": api_key},
                timeout=REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
            publish_event("media.recommendation.added", {
                "title": rec.item.title,
                "service": "sonarr",
                "score": rec.score,
            })
            logger.info("auto_add_to_sonarr: added '%s'", rec.item.title)
            return True
        except Exception as exc:
            logger.error("auto_add_to_sonarr '%s': %s", rec.item.title, exc)
            return False

    def auto_add_to_radarr(self, rec: Recommendation, radarr_url: str, api_key: str) -> bool:
        """Add a recommended movie to Radarr.

        Args:
            rec: Recommendation containing a ContentItem of type 'movie'.
            radarr_url: Base URL for the Radarr instance.
            api_key: Radarr API key.

        Returns:
            True if the movie was successfully added.
        """
        if not _REQUESTS_AVAILABLE:
            logger.warning("auto_add_to_radarr: requests unavailable")
            return False
        if rec.item.type != "movie":
            logger.warning("auto_add_to_radarr: item '%s' is not a movie", rec.item.title)
            return False
        try:
            payload = {
                "title": rec.item.title,
                "year": rec.item.year,
                "tmdbId": rec.item.tmdb_id,
                "qualityProfileId": 1,
                "rootFolderPath": "/movies",
                "addOptions": {"searchForMovie": True},
                "monitored": True,
            }
            resp = requests.post(
                f"{radarr_url.rstrip('/')}/api/v3/movie",
                json=payload,
                headers={"X-Api-Key": api_key},
                timeout=REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
            publish_event("media.recommendation.added", {
                "title": rec.item.title,
                "service": "radarr",
                "score": rec.score,
            })
            logger.info("auto_add_to_radarr: added '%s'", rec.item.title)
            return True
        except Exception as exc:
            logger.error("auto_add_to_radarr '%s': %s", rec.item.title, exc)
            return False
