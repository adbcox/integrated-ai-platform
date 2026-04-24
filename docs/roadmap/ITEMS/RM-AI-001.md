# RM-AI-001

- **ID:** `RM-AI-001`
- **Title:** Local translation service with offline-first architecture
- **Category:** `AI`
- **Type:** `System`
- **Status:** `Planned`
- **Maturity:** `M0`
- **Priority:** `High`
- **Priority class:** `P2`
- **Queue rank:** `TBD`
- **Target horizon:** `soon`
- **LOE:** `M`
- **Strategic value:** `4`
- **Architecture fit:** `4`
- **Execution risk:** `2`
- **Dependency burden:** `2`
- **Readiness:** `near`

## Description

Build local, self-hosted translation service providing offline-first multilingual support via LibreTranslate as primary platform with fallback to NLLB-200 and TranslateGemma via Ollama for edge deployment.

This item establishes the reusable translation substrate for platform internationalization, document processing, and cross-lingual intelligence.

## Why it matters

Platform currently lacks a local translation service, requiring:
- external cloud APIs for any translation work (cost, latency, privacy),
- internet connectivity for translated content (breaks offline operation),
- manual content translation and localization,
- inability to support non-English user bases or multilingual workflows.

Without this foundation, platform is English-only and dependent on external services.

## Reuse-first implementation approach

This item follows explicit reuse-first posture per `docs/architecture/OSS_REUSE_AND_ADOPTION_REGISTER.md`.

**Primary choice: LibreTranslate (self-hosted)**
- Reason: 100+ language pairs, offline-capable, MIT license, Docker-native, no cloud dependency, REST API
- Mode: Adopt as full product
- Deployment: Docker container (`LibreTranslate/LibreTranslate`)
- Models: Multiple backend options (Argos, CTransformers)
- Performance: Lightweight (1-4GB RAM depending on model), CPU-friendly
- Configuration: Environment variables, flexible model selection

**Secondary choice: NLLB-200 (Meta)**
- Reason: 200+ language support (multilingual), open-source, state-of-the-art accuracy
- Mode: Adopt selectively for high-accuracy translation
- Integration: Serve via Ollama or vLLM
- Model: 600M and 3.3B variants (balance speed/accuracy)
- Performance: ~2-5 seconds per sentence on CPU

**Tertiary choice: TranslateGemma (Google)**
- Reason: Lightweight (2B/9B), fast inference, good quality for edge
- Mode: Adopt selectively for low-resource environments
- Integration: Serve via Ollama
- Model: 2B (mobile/edge), 9B (better accuracy)
- Performance: Optimized for Ollama (very fast on consumer hardware)

**Not to rebuild:**
- translation models or training,
- language detection (LibreTranslate built-in),
- API gateway or load balancing.

## Key requirements

### Core translation service requirements
- Deploy LibreTranslate as primary service
- Support 100+ language pairs (LibreTranslate supported list)
- Expose REST API for translation requests
- Language detection for input text
- Batch translation support (multiple texts per request)
- Translation quality metrics (optional scoring)
- Cache frequently translated content
- Support character encoding (UTF-8, ISO-8859-1, etc.)

### Model deployment requirements
- LibreTranslate with default Argos models
- Fallback to NLLB-200 (600M model for balance)
- Ollama integration for TranslateGemma (2B for edge)
- Model storage and caching
- Automatic model download on first use
- Memory management (unload unused models)
- GPU acceleration support (optional)

### API and integration requirements
- REST endpoints:
  - POST /translate — Translate text
  - GET /languages — List supported languages
  - POST /detect — Detect language
  - POST /batch — Translate multiple texts
- Integration with dashboard (RM-UI-001)
- Webhook support for async translation
- API authentication (token-based)
- Rate limiting and quota management
- Translation history and audit logging

### Performance and reliability requirements
- Single translation: < 1 second for short text (< 100 chars)
- Batch of 100 sentences: < 30 seconds
- Batch of 1000 sentences: < 5 minutes
- CPU only: acceptable (LibreTranslate optimized)
- GPU optional: 2-4GB VRAM if available
- Memory: 2GB minimum (LibreTranslate), 4GB+ with NLLB
- Fallback to simpler model if primary overloaded
- Health checks and auto-restart on failure

### Localization and internationalization requirements
- Support platform UI internationalization
- Translate user-facing strings on demand
- Document and content translation
- Preserve formatting in translated content (markdown, HTML)
- Handle special characters and diacritics
- Language-specific sorting and collation (optional)
- RTL language support (Arabic, Hebrew) if needed

### Security and privacy requirements
- All translation happens locally (no cloud APIs)
- No logging of sensitive content (optional PII redaction)
- API access controlled via authentication tokens
- HTTPS for inter-service communication
- Audit trail for compliance workflows
- Retention policies for translation history

## Affected systems

- Platform internationalization and localization
- Document processing and intelligence
- User interface and content delivery
- Automation and workflow engines
- Multi-language support for users/teams
- Cross-lingual knowledge systems

## Expected file families

- `config/translation/` — Translation service configuration
  - `libretranslate.yaml` — Service settings
  - `models.yaml` — Model selection and fallbacks
- `framework/translation_service.py` — Translation abstraction layer
  - `libretranslate_adapter.py` — LibreTranslate integration
  - `nllb_adapter.py` — NLLB-200 integration
  - `ollama_translation_adapter.py` — Ollama-served models
  - `translation_cache.py` — Caching and optimization
- `docker/docker-compose-translation.yml` — Service deployment
- `docs/runbooks/TRANSLATION_SERVICE_DEPLOYMENT.md` — Setup guide
- `docs/runbooks/TRANSLATION_PERFORMANCE_TUNING.md` — Optimization guide
- `tools/translate_batch.py` — CLI tool for batch translation
- `tests/test_translation_service.py` — Integration tests

## Dependencies

- Docker and Docker Compose
- Python 3.11+
- LibreTranslate Docker image
- Ollama (optional, for fallback models)
- Platform API infrastructure
- Job queueing system (for async translation)

## External dependencies

### LibreTranslate
- **Official site:** https://libretranslate.com/
- **Repo:** https://github.com/LibreTranslate/LibreTranslate
- **Docker image:** `ghcr.io/libretranslate/libretranslate:latest`
- **License:** AGPL (can be waived with commercial license)
- **Languages:** 100+ language pairs
- **Backend:** Argos Machine Translation (default)
- **Resource usage:** 2GB RAM, CPU-friendly
- **API:** REST endpoints, simple JSON
- **Deployment:** Single Docker container, no external dependencies
- **Adoption note:** `adopt-now` as primary translation platform

### NLLB-200 (Meta)
- **Official:** https://github.com/facebookresearch/fairseq/tree/nllb
- **Languages:** 200+ language coverage
- **Models:** 600M (distilled, fast) and 3.3B (full, accurate)
- **Inference frameworks:** PyTorch, ONNX, TensorRT
- **Performance:** ~2-5 seconds per sentence on CPU
- **Accuracy:** State-of-the-art for multilingual translation
- **Integration:** Serve via vLLM or Ollama
- **Adoption note:** `adopt-selective` for high-accuracy scenarios

### TranslateGemma
- **Source:** Google (via Ollama)
- **Models:** 2B (lightweight), 9B (balanced)
- **Inference:** Optimized for Ollama, very fast
- **Languages:** 200+ supported
- **Use case:** Edge deployment, mobile, low-resource
- **Performance:** <500ms per sentence on consumer hardware
- **Integration:** Via Ollama (`ollama pull translategemma:2b`)
- **Adoption note:** `adopt-selective` for edge/mobile scenarios

### Ollama
- **Official site:** https://ollama.ai/
- **Purpose:** Lightweight model serving for translation fallback
- **Models:** Supports TranslateGemma, NLLB-200
- **Adoption note:** `adopt-selective` as LibreTranslate fallback

## First milestone

Translation service with:
1. LibreTranslate deployed and running
2. REST API for translation (POST /translate)
3. Language detection working (GET /detect)
4. 50+ language pairs tested
5. API accessible from platform services
6. Basic caching for repeated translations
7. Health checks and monitoring
8. Documentation for service usage

## Autonomous execution guidance

### Pre-implementation
1. Verify Docker and Docker Compose available
2. Assess hardware (CPU sufficient, GPU optional)
3. Identify translation use cases (UI, documents, content)
4. Choose deployment approach (LibreTranslate only, or with fallbacks)
5. Plan for model storage (~5-10GB per model)

### Implementation sequence
1. **LibreTranslate deployment:**
   - Create `docker/docker-compose-translation.yml`
   - Deploy LibreTranslate container
   - Configure environment variables (API key, allowed languages)
   - Set resource limits (memory, CPU)
   - Configure health checks
   - Test API connectivity

2. **Translation service framework:**
   - Create `framework/translation_service.py`
   - Implement `LibreTranslateAdapter` wrapper
   - Add caching layer (Redis or in-memory)
   - Implement language detection
   - Add error handling and fallback logic

3. **API endpoints:**
   - POST /translate — Core translation endpoint
   - GET /languages — List supported language pairs
   - GET /detect — Detect input language
   - POST /batch — Batch translation
   - GET /health — Service health check

4. **Caching and optimization:**
   - Cache frequent translations (Redis if available, else in-memory)
   - Batch API calls to reduce overhead
   - Implement TTL for cached translations
   - Monitor cache hit rates

5. **Optional fallback models:**
   - Deploy NLLB-200 (600M) via vLLM or PyTorch if high-accuracy needed
   - Deploy TranslateGemma via Ollama for edge scenarios
   - Implement fallback routing (primary → secondary)
   - Load balance across models based on availability

6. **Integration:**
   - Expose endpoints to platform services
   - Add translation support to dashboard (RM-UI-001)
   - Document API for tool integration
   - Connect to automation/workflow engines

7. **Testing and validation:**
   - Test basic translation (English → Spanish, etc.)
   - Test 20+ language pairs
   - Test language detection accuracy
   - Benchmark latency (single, batch)
   - Validate accuracy on sample documents
   - Test fallback when primary overloaded

8. **Documentation:**
   - Create `docs/runbooks/TRANSLATION_SERVICE_DEPLOYMENT.md`
   - Document language pair support
   - Document performance characteristics
   - Document troubleshooting (model loading, memory issues)

### Completion contract
- LibreTranslate deployed and operational
- Translation API endpoints functional
- At least 50 language pairs working
- Language detection working correctly
- Caching reducing repeated translation latency
- Fallback model strategy defined (if using NLLB/TranslateGemma)
- Health checks and monitoring active
- Documentation complete

## Status transition

- Expected next status: `In Progress`
- Transition condition: Docker infrastructure ready, first use case identified, resource availability confirmed
- Validation/closeout condition: Translation service responding to requests, multiple languages working, caching active, integration points documented

## Notes

Translation service enables:
- Platform internationalization (UI, content)
- Multilingual user support
- Document translation and processing
- Cross-lingual content and knowledge systems
- Offline operation (no cloud dependency)

Architecture decision:
- LibreTranslate chosen as primary for simplicity and self-hosting
- NLLB-200 added as secondary for accuracy-critical workflows
- TranslateGemma for edge/low-resource deployment
- Ollama provides common fallback infrastructure

Performance profile:
- LibreTranslate: ~1-2 seconds per paragraph on CPU
- NLLB-200: ~2-5 seconds per sentence on CPU (more accurate)
- TranslateGemma: <500ms per sentence on consumer CPU
- All models substantially faster on GPU

Risk mitigation:
- Primary service failure → fallback to lighter NLLB or TranslateGemma
- Model loading timeout → implement async loading with default translations
- Unsupported language pair → graceful error response, no broken UI
- Memory pressure → implement model unloading and selective loading

Privacy and security:
- All translation local (no external APIs)
- No persistent logging of content (audit trail optional)
- API authentication required
- Suitable for sensitive content (PII, legal documents)
