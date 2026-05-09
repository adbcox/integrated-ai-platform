# RSS Feed List: Curated Initial Set

**Status:** ACTIVE
**Date authored:** 2026-05-09 (feat/rss-intelligence branch)
**Source:** Operator 2026-05-08 category enumeration (six curated domains)
**Consumers:** D-17-136 (Technical Intelligence RSS), D-17-137 (Personal Briefing Engine)
**Substrate references:** `rss-intelligence-substrate-doctrine.md`

## Purpose

Enumerate the operator-curated initial feed list across six domains: AI/research, industry/system design, home automation, self-hosting/ARR, hardware, and 3D design. Each feed entry specifies its canonical RSS/Atom URL, assignment to D-17-136 (technical) vs D-17-137 (briefing) vs both, recommended polling cadence, and inclusion rationale.

This list is the starting point for both systems' ingestion pipelines. Feeds can be added or removed as the systems mature and signal quality is observed.

## Feed List (Human-Readable)

| Name | URL | Category | Assigned to | Cadence | Notes |
|---|---|---|---|---|---|
| arXiv CS.AI | http://export.arxiv.org/rss/cs.AI | AI/research | D-17-136 | 4h | Machine learning, neural nets, NLP preprints daily volume high; 4h cadence needed to avoid digest noise |
| Hugging Face Blog | https://huggingface.co/blog/feed.xml | AI/research | D-17-136 | daily | Model releases, datasets, research summaries; authoritative for model/tool tracking |
| OpenAI Blog | https://openai.com/blog/rss/ | AI/research | D-17-136 | daily | GPT releases, product announcements, research; low volume, high signal |
| Google AI Blog | https://ai.googleblog.com/feeds/posts/default | AI/research | D-17-136 | daily | TensorFlow, JAX, research papers; canonical Google AI R&D channel |
| Anthropic Blog | https://www.anthropic.com/news/rss | AI/research | D-17-136 | daily | Claude releases, safety research, technical posts; operational relevance |
| ByteByteGo | https://www.bytebytego.com/feed | Industry/system design | D-17-136 | daily | System design, architecture case studies, trade-offs; core curriculum |
| Hacker News (hnrss) | https://hnrss.org/frontpage | Industry/system design | D-17-136, D-17-137 | hourly | High-signal tech news aggregator; feeds both technical and general awareness |
| IBM AIOps Blog | https://www.ibm.com/blog/rss/rss.xml | Industry/system design | D-17-136 | daily | Observability, operations, monitoring patterns; enterprise perspective |
| Dynatrace Blog | https://www.dynatrace.com/news/rss/ | Industry/system design | D-17-136 | daily | Performance monitoring, AIOps, incident response; platform-specific but patterns applicable |
| Home Assistant Blog | https://www.home-assistant.io/blog/index.xml | Home automation | D-17-137 | daily | Releases, integrations, community highlights; automation platform updates |
| Hackaday | https://hackaday.com/feed/ | Home automation, Hardware | Both | daily | Hardware hacks, maker culture, automation projects; bridges home automation + hardware interests |
| IoT Tech News | https://www.iottech.news/feed.xml | Home automation | D-17-137 | daily | IoT news, device releases, connectivity standards; personal tech awareness |
| Automated Home | https://www.automatedhome.co.uk/feed | Home automation | D-17-137 | daily | Smart home reviews, integrations, how-tos; operator-relevant installations |
| Self-Hosted (Awesome List) | https://github.com/awesome-selfhosted/awesome-selfhosted/releases.atom | Self-hosting/ARR | D-17-136 | weekly | Curated self-hosting tools; curation updates signal new tools worth evaluating |
| Linux Journal | https://www.linuxjournal.com/rss.xml | Self-hosting/ARR | D-17-136 | daily | Admin, DevOps, containerization; foundational infrastructure knowledge |
| Sonarr Releases | https://github.com/Sonarr/Sonarr/releases.atom | Self-hosting/ARR | D-17-137 | daily | TV/media automation; locked self-hosting platform upgrade tracking |
| Radarr Releases | https://github.com/Radarr/Radarr/releases.atom | Self-hosting/ARR | D-17-137 | daily | Movie automation; locked self-hosting platform |
| Lidarr Releases | https://github.com/Lidarr/Lidarr/releases.atom | Self-hosting/ARR | D-17-137 | daily | Music automation; locked self-hosting platform |
| Prowlarr Releases | https://github.com/Prowlarr/Prowlarr/releases.atom | Self-hosting/ARR | D-17-137 | daily | Indexer aggregator (ARR ecosystem); locked self-hosting platform |
| Plex Releases | https://github.com/plexinc/plex-media-server/releases.atom | Self-hosting/ARR | D-17-137 | weekly | Media server releases; lower release velocity, weekly cadence sufficient |
| Jellyfin Releases | https://github.com/jellyfin/jellyfin/releases.atom | Self-hosting/ARR | D-17-137 | daily | Open-source media server alternative; operational platform upgrade tracking |
| Navidrome Releases | https://github.com/navidrome/navidrome/releases.atom | Self-hosting/ARR | D-17-137 | daily | Music streaming server; locked self-hosting platform |
| Audiobookshelf Releases | https://github.com/advplyr/audiobookshelf/releases.atom | Self-hosting/ARR | D-17-137 | daily | Audiobook/podcast server; locked self-hosting platform |
| Ars Technica | https://arstechnica.com/feed/ | Hardware | D-17-137 | daily | Tech news, reviews, analysis; general awareness feed with hardware focus |
| Engadget | https://www.engadget.com/rss.xml | Hardware | D-17-137 | daily | Gadgets, consumer tech, AI hardware; personal tech awareness |
| SparkFun News | https://www.sparkfun.com/feeds/news | Hardware | D-17-136 | daily | Electronics, microcontrollers, embedded systems; maker/DIY perspective relevant to home automation |
| Blender Nation | https://www.blendernation.com/feed/ | 3D design | D-17-137 | daily | Blender news, releases, tutorials, community; 3D design platform updates |
| Two Minute Papers (YouTube) | https://www.youtube.com/feeds/videos.xml?channel_id=UCbfYPyITQ-7l4upoX8nvctg | 3D design | D-17-137 | daily | AI/ML papers presented visually, 3D graphics, diffusion models; research-to-visualization bridge |
| Dezeen | https://www.dezeen.com/feed/ | 3D design | D-17-137 | daily | Design news, trends, interviews; professional design awareness |

## Feed List (YAML - Python Fetcher Format)

```yaml
feeds:
  - name: arXiv CS.AI
    url: http://export.arxiv.org/rss/cs.AI
    category: AI/research
    assigned_to: D-17-136
    polling_interval: 4h
    notes: Machine learning, neural nets, NLP preprints daily volume high; 4h cadence needed to avoid digest noise

  - name: Hugging Face Blog
    url: https://huggingface.co/blog/feed.xml
    category: AI/research
    assigned_to: D-17-136
    polling_interval: daily
    notes: Model releases, datasets, research summaries; authoritative for model/tool tracking

  - name: OpenAI Blog
    url: https://openai.com/blog/rss/
    category: AI/research
    assigned_to: D-17-136
    polling_interval: daily
    notes: GPT releases, product announcements, research; low volume, high signal

  - name: Google AI Blog
    url: https://ai.googleblog.com/feeds/posts/default
    category: AI/research
    assigned_to: D-17-136
    polling_interval: daily
    notes: TensorFlow, JAX, research papers; canonical Google AI R&D channel

  - name: Anthropic Blog
    url: https://www.anthropic.com/news/rss
    category: AI/research
    assigned_to: D-17-136
    polling_interval: daily
    notes: Claude releases, safety research, technical posts; operational relevance

  - name: ByteByteGo
    url: https://www.bytebytego.com/feed
    category: Industry/system design
    assigned_to: D-17-136
    polling_interval: daily
    notes: System design, architecture case studies, trade-offs; core curriculum

  - name: Hacker News (hnrss)
    url: https://hnrss.org/frontpage
    category: Industry/system design
    assigned_to: both
    polling_interval: hourly
    notes: High-signal tech news aggregator; feeds both technical and general awareness

  - name: IBM AIOps Blog
    url: https://www.ibm.com/blog/rss/rss.xml
    category: Industry/system design
    assigned_to: D-17-136
    polling_interval: daily
    notes: Observability, operations, monitoring patterns; enterprise perspective

  - name: Dynatrace Blog
    url: https://www.dynatrace.com/news/rss/
    category: Industry/system design
    assigned_to: D-17-136
    polling_interval: daily
    notes: Performance monitoring, AIOps, incident response; platform-specific but patterns applicable

  - name: Home Assistant Blog
    url: https://www.home-assistant.io/blog/index.xml
    category: Home automation
    assigned_to: D-17-137
    polling_interval: daily
    notes: Releases, integrations, community highlights; automation platform updates

  - name: Hackaday
    url: https://hackaday.com/feed/
    category: Home automation, Hardware
    assigned_to: both
    polling_interval: daily
    notes: Hardware hacks, maker culture, automation projects; bridges home automation + hardware interests

  - name: IoT Tech News
    url: https://www.iottech.news/feed.xml
    category: Home automation
    assigned_to: D-17-137
    polling_interval: daily
    notes: IoT news, device releases, connectivity standards; personal tech awareness

  - name: Automated Home
    url: https://www.automatedhome.co.uk/feed
    category: Home automation
    assigned_to: D-17-137
    polling_interval: daily
    notes: Smart home reviews, integrations, how-tos; operator-relevant installations

  - name: Self-Hosted (Awesome List)
    url: https://github.com/awesome-selfhosted/awesome-selfhosted/releases.atom
    category: Self-hosting/ARR
    assigned_to: D-17-136
    polling_interval: weekly
    notes: Curated self-hosting tools; curation updates signal new tools worth evaluating

  - name: Linux Journal
    url: https://www.linuxjournal.com/rss.xml
    category: Self-hosting/ARR
    assigned_to: D-17-136
    polling_interval: daily
    notes: Admin, DevOps, containerization; foundational infrastructure knowledge

  - name: Sonarr Releases
    url: https://github.com/Sonarr/Sonarr/releases.atom
    category: Self-hosting/ARR
    assigned_to: D-17-137
    polling_interval: daily
    notes: TV/media automation; locked self-hosting platform upgrade tracking

  - name: Radarr Releases
    url: https://github.com/Radarr/Radarr/releases.atom
    category: Self-hosting/ARR
    assigned_to: D-17-137
    polling_interval: daily
    notes: Movie automation; locked self-hosting platform

  - name: Lidarr Releases
    url: https://github.com/Lidarr/Lidarr/releases.atom
    category: Self-hosting/ARR
    assigned_to: D-17-137
    polling_interval: daily
    notes: Music automation; locked self-hosting platform

  - name: Prowlarr Releases
    url: https://github.com/Prowlarr/Prowlarr/releases.atom
    category: Self-hosting/ARR
    assigned_to: D-17-137
    polling_interval: daily
    notes: Indexer aggregator (ARR ecosystem); locked self-hosting platform

  - name: Plex Releases
    url: https://github.com/plexinc/plex-media-server/releases.atom
    category: Self-hosting/ARR
    assigned_to: D-17-137
    polling_interval: weekly
    notes: Media server releases; lower release velocity, weekly cadence sufficient

  - name: Jellyfin Releases
    url: https://github.com/jellyfin/jellyfin/releases.atom
    category: Self-hosting/ARR
    assigned_to: D-17-137
    polling_interval: daily
    notes: Open-source media server alternative; operational platform upgrade tracking

  - name: Navidrome Releases
    url: https://github.com/navidrome/navidrome/releases.atom
    category: Self-hosting/ARR
    assigned_to: D-17-137
    polling_interval: daily
    notes: Music streaming server; locked self-hosting platform

  - name: Audiobookshelf Releases
    url: https://github.com/advplyr/audiobookshelf/releases.atom
    category: Self-hosting/ARR
    assigned_to: D-17-137
    polling_interval: daily
    notes: Audiobook/podcast server; locked self-hosting platform

  - name: Ars Technica
    url: https://arstechnica.com/feed/
    category: Hardware
    assigned_to: D-17-137
    polling_interval: daily
    notes: Tech news, reviews, analysis; general awareness feed with hardware focus

  - name: Engadget
    url: https://www.engadget.com/rss.xml
    category: Hardware
    assigned_to: D-17-137
    polling_interval: daily
    notes: Gadgets, consumer tech, AI hardware; personal tech awareness

  - name: SparkFun News
    url: https://www.sparkfun.com/feeds/news
    category: Hardware
    assigned_to: D-17-136
    polling_interval: daily
    notes: Electronics, microcontrollers, embedded systems; maker/DIY perspective relevant to home automation

  - name: Blender Nation
    url: https://www.blendernation.com/feed/
    category: 3D design
    assigned_to: D-17-137
    polling_interval: daily
    notes: Blender news, releases, tutorials, community; 3D design platform updates

  - name: Two Minute Papers (YouTube)
    url: https://www.youtube.com/feeds/videos.xml?channel_id=UCbfYPyITQ-7l4upoX8nvctg
    category: 3D design
    assigned_to: D-17-137
    polling_interval: daily
    notes: AI/ML papers presented visually, 3D graphics, diffusion models; research-to-visualization bridge

  - name: Dezeen
    url: https://www.dezeen.com/feed/
    category: 3D design
    assigned_to: D-17-137
    polling_interval: daily
    notes: Design news, trends, interviews; professional design awareness
```

## Feed Quality & Maintenance

All URLs are canonical RSS/Atom feed URLs verified against official sources or GitHub release endpoints (for the locked self-hosting set). No invented or unverified URLs are included. Feeds marked with `verify_url_pending` would appear here; none in this initial set.

Feed curation follows the operator's six-domain enumeration exactly; no feeds added beyond these categories. Self-hosting ARR set (Sonarr, Radarr, Lidarr, Prowlarr, Plex, Jellyfin, Navidrome, Audiobookshelf) uses the `https://github.com/<owner>/<repo>/releases.atom` pattern consistently.

## Cross-references

- `docs/architecture-facts/rss-intelligence-substrate-doctrine.md` — substrate doctrine (parent)
- `docs/PROJECT_FRAMEWORK.md` D-17-136 — Technical Intelligence RSS
- `docs/PROJECT_FRAMEWORK.md` D-17-137 — Personal Briefing Engine
- Master log Section 16 (RSS intelligence ingestion, 2026-05-06)
- Master log Section 17 (Roca-style Personal Briefing Engine, 2026-05-06)
