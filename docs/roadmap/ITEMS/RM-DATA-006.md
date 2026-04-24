# RM-DATA-006

- **ID:** `RM-DATA-006`
- **Title:** OCR and document intelligence pipeline for vision models and batch processing
- **Category:** `DATA`
- **Type:** `System`
- **Status:** `Planned`
- **Maturity:** `M0`
- **Priority:** `High`
- **Priority class:** `P2`
- **Queue rank:** `TBD`
- **Target horizon:** `soon`
- **LOE:** `M`
- **Strategic value:** `5`
- **Architecture fit:** `5`
- **Execution risk:** `2`
- **Dependency burden:** `2`
- **Readiness:** `near`

## Description

Build infrastructure-level OCR and document intelligence pipeline combining vision models (Qwen3-VL, DeepSeek-OCR 2, Gemma 4) with batch processing engines (Marker, Docling, PaddleOCR) for handwriting recognition, screenshot extraction, and PDF digitization.

This item establishes the reusable document processing substrate for platform intelligence, information extraction, and knowledge base ingestion.

## Why it matters

Platform currently lacks a unified document intelligence system that:
- extracts text from handwritten documents and screenshots,
- digitizes PDFs and scanned documents at scale,
- recognizes structured data (forms, tables, invoices),
- processes documents locally without external APIs,
- integrates with platform knowledge systems and automation.

Without this foundation, document-based workflows require manual transcription or external services, limiting automation and knowledge extraction capabilities.

## Reuse-first implementation approach

This item follows explicit reuse-first posture per `docs/architecture/OSS_REUSE_AND_ADOPTION_REGISTER.md`.

**Primary choice: Marker (VT-2.5 or VT-1.4)**
- Reason: State-of-the-art PDF-to-markdown conversion, table/layout preservation, 95%+ accuracy, active development, minimal dependencies
- Mode: Adopt as full product for PDF processing
- Integration: Python library or API via vLLM server
- Performance: ~2-5 seconds per page on GPU, ~30 seconds on CPU
- Resource: GPU preferred (4GB+ VRAM), CPU fallback acceptable

**Secondary choice: Docling (IBM)**
- Reason: End-to-end document understanding, layout-preserving export, supports PDF/TIFF/PNG, enterprise-grade
- Mode: Adopt selectively for complex layouts and structured extraction
- Integration: Python library with model auto-download
- Performance: Heavy but comprehensive (layout, tables, formulas)

**Vision models for intelligence:**
- **Qwen3-VL** — Best cost/performance for document vision tasks, 1.5M token context
- **DeepSeek-OCR 2** — Specialized OCR accuracy, low latency
- **Gemma 4** — Lightweight alternative (8B), good for edge deployment
- Mode: Serve via vLLM, fallback to Ollama for local-only scenarios

**Not to rebuild:**
- PDF parsing and layout analysis,
- OCR engines (use industry standard),
- vision model training,
- language models.

## Key requirements

### Core OCR pipeline requirements
- Deploy Marker for PDF-to-markdown conversion
- Integrate Docling for complex document understanding
- Deploy vision model server via vLLM (Qwen3-VL primary)
- Establish fallback to Ollama for offline scenarios
- Support batch processing of 50-1000 documents
- Queue and scheduling for long-running jobs
- Track processing metrics: accuracy, latency, resource usage

### Document format support
- PDF files (scanned and digital)
- Image files (PNG, JPEG, TIFF)
- Handwritten document images
- Screenshots with text
- Multi-page batch processing
- Output: Markdown, structured JSON, plaintext fallback

### Vision model requirements
- Qwen3-VL as primary inference engine
- Support document layout understanding
- Extract text, tables, formulas
- Recognize handwriting
- Identify document type and structure
- Fallback to Gemma 4 or DeepSeek-OCR 2 if vLLM unavailable
- Model quantization for local deployment (4-bit, 8-bit options)

### Batch processing requirements
- Queue-based document processing
- Parallel processing of multiple documents
- Job status tracking and retry logic
- Resource-aware scheduling (don't overload GPU/CPU)
- Progress reporting via platform APIs
- Failed document handling and logging
- Completion callbacks to trigger downstream tasks

### Integration point requirements
- Expose OCR results to knowledge base ingestion (RM-DATA-*)
- Surface extraction results to automation engine (RM-OPS-*)
- Make OCR accessible via platform APIs for tools/dashboards
- Support webhook notifications for completed jobs
- Integrate with platform file storage (document versioning)
- Connect to learning loops (improved recognition over time)

### Security and privacy requirements
- All processing happens locally (no cloud OCR)
- Document access controlled via platform permissions
- Sensitive document handling (PII masking optional)
- No model training on user documents
- Audit logging for document access
- Retention policies for processed documents

### Performance and scalability requirements
- Single document: < 5 seconds on GPU, < 30 seconds on CPU
- Batch of 100 documents: < 10 minutes on GPU
- Support queue size of 1000+ documents
- Memory efficient (stream processing, not all-in-memory)
- GPU memory: 4-8GB minimum (Qwen3-VL)
- CPU fallback: 8GB RAM minimum
- Horizontal scaling via worker processes/containers

## Affected systems

- Document processing infrastructure layer
- Knowledge base ingestion and indexing
- Automation and workflow engines
- File management and storage layer
- Intelligence and reasoning systems
- Platform APIs for tool integrations

## Expected file families

- `config/ocr/` — OCR pipeline configuration
  - `marker.yaml` — PDF processing settings
  - `docling.yaml` — Complex document settings
  - `vision_models.yaml` — Vision model routing and fallbacks
- `framework/ocr_pipeline.py` — Core OCR orchestration
  - `ocr_service.py` — Unified OCR interface
  - `marker_adapter.py` — Marker integration
  - `docling_adapter.py` — Docling integration
  - `vision_adapter.py` — Vision model inference
- `framework/document_queue.py` — Job queueing and scheduling
- `docker/docker-compose-ocr.yml` — vLLM server and workers
- `docs/runbooks/OCR_PIPELINE_DEPLOYMENT.md` — Deployment guide
- `docs/runbooks/OCR_MODEL_SELECTION.md` — Model selection and tuning
- `.env.ocr` — Model paths, API endpoints, resource limits

## Dependencies

- vLLM server for vision model inference (or Ollama alternative)
- GPU infrastructure (4GB+ VRAM recommended)
- Python 3.11+
- `RM-DATA-*` — Knowledge base and indexing systems
- `RM-OPS-*` — Automation and job scheduling
- Docker and Docker Compose (for vLLM server)

## External dependencies

### Marker
- **Official repo:** https://github.com/VikParuchuri/marker
- **Version:** VT-2.5 (latest) or VT-1.4 (stable)
- **Mode:** Adopt as full product
- **Performance:** 95%+ accuracy on PDFs, layout preservation
- **Requirements:** PyTorch, Tesseract OCR (optional for hybrid mode)
- **Deployment:** Python library or Docker container
- **Adoption note:** `adopt-now` as primary PDF processor

### Docling
- **Official repo:** https://github.com/IBM/docling
- **Version:** 2.0+
- **Mode:** Adopt selectively for complex documents
- **Features:** Layout preservation, structured extraction, formula recognition
- **Requirements:** ONNX Runtime, layout analysis models
- **Deployment:** Python library with automatic model download
- **Adoption note:** `adopt-selective` for enterprise document processing

### vLLM
- **Official site:** https://www.vllm.ai/
- **Repo:** https://github.com/vLLM-project/vLLM
- **Purpose:** High-throughput inference server for vision models
- **Models:** Supports Qwen, DeepSeek, Gemma
- **Deployment:** Docker container with GPU support
- **Performance:** 10-100x faster than HuggingFace transformers
- **Adoption note:** `adopt-now` for vision model serving

### Qwen3-VL
- **Model:** https://huggingface.co/Qwen/Qwen3-VL-14B
- **Capability:** Document understanding, handwriting, tables
- **Context:** 1.5M tokens
- **Quantization:** Supports 4-bit and 8-bit variants
- **Performance:** ~500ms per image on A100, ~2s on RTX 4090
- **Adoption note:** `adopt-now` as primary vision model

### DeepSeek-OCR 2
- **Model:** DeepSeek-OCR 2 (specialized OCR)
- **Capability:** High-accuracy OCR, layout preservation
- **Lightweight:** 8B model available
- **Adoption note:** `adopt-selective` as OCR specialist alternative

### Ollama
- **Official site:** https://ollama.ai/
- **Purpose:** Local model serving fallback
- **Use case:** Offline scenarios, no vLLM available
- **Models:** Supports Qwen, Gemma, DeepSeek
- **Adoption note:** `adopt-selective` as vLLM fallback

## First milestone

OCR pipeline with:
1. Marker deployed for PDF processing
2. vLLM server with Qwen3-VL running
3. Document upload and processing queue
4. Single document OCR working end-to-end
5. Output: Markdown with preserved layout
6. Batch processing of 10-50 documents
7. Status API and job tracking
8. Basic metrics (latency, accuracy)

## Autonomous execution guidance

### Pre-implementation
1. Verify GPU availability or estimate CPU timeline
2. Confirm vLLM server deployment infrastructure ready
3. Check knowledge base integration points (RM-DATA-*)
4. Identify first use case (PDF digitization, handwriting, screenshots)
5. Collect sample documents for testing

### Implementation sequence
1. **Environment setup:**
   - Install vLLM with vision model support
   - Download Qwen3-VL model (40GB+ disk space)
   - Install Marker and Docling Python packages
   - Configure GPU memory limits and quantization if needed

2. **vLLM server deployment:**
   - Create `docker/docker-compose-ocr.yml`
   - Deploy vLLM container with Qwen3-VL
   - Configure API endpoint and authentication
   - Health checks and resource monitoring
   - Setup Ollama fallback on separate port

3. **OCR pipeline framework:**
   - Create `framework/ocr_pipeline.py` orchestrator
   - Implement Marker adapter (PDF → Markdown)
   - Implement Docling adapter (complex documents)
   - Implement vision model adapter (via vLLM)
   - Build fallback routing logic

4. **Job queue and scheduling:**
   - Create `framework/document_queue.py`
   - Integrate with platform job scheduler
   - Track processing status (queued, processing, complete, failed)
   - Implement retry logic with backoff
   - Add webhook notifications

5. **API and integration:**
   - Expose OCR endpoints:
     - POST /ocr/upload — Submit document
     - GET /ocr/job/{id} — Check status
     - GET /ocr/result/{id} — Retrieve results
   - Integrate with knowledge base ingestion
   - Connect to platform dashboards for monitoring

6. **Testing and validation:**
   - Test with sample PDFs (scanned, digital, mixed)
   - Test with handwritten document images
   - Test with screenshots and complex layouts
   - Benchmark performance: latency, accuracy, resource usage
   - Validate batch processing (50+ documents)
   - Test fallback to Ollama (if vLLM unavailable)

7. **Documentation:**
   - Create `docs/runbooks/OCR_PIPELINE_DEPLOYMENT.md`
   - Document model selection (when to use each vision model)
   - Document performance tuning and resource limits
   - Document troubleshooting (CUDA errors, memory issues, inference failures)

### Completion contract
- OCR pipeline deployed and accessible via API
- Single document processing working end-to-end
- Batch processing of 50+ documents functional
- Marker and vLLM deployed and healthy
- Fallback to Ollama or CPU working
- Status tracking and metrics collection active
- At least 3 document types tested (PDF, handwriting, screenshot)
- Integration point with knowledge base ready
- Deployment runbook complete and validated

## Status transition

- Expected next status: `In Progress`
- Transition condition: GPU/CPU infrastructure verified, vLLM deployment path clear, first use case identified
- Validation/closeout condition: OCR pipeline processing documents, batch jobs tracking correctly, metrics visible, fallback working

## Notes

OCR pipeline is critical infrastructure for:
- Knowledge base ingestion from documents
- Automation workflows triggered by document content
- Screenshot and handwriting recognition
- Form and invoice processing

Performance considerations:
- GPU strongly recommended for <5s latency per document
- CPU fallback acceptable for batch/offline processing
- Qwen3-VL chosen for best accuracy/cost balance
- Model quantization (4-bit/8-bit) reduces VRAM needs

Security posture:
- All processing local (no cloud APIs)
- Document access controlled
- Audit logging for compliance
- PII masking optional for sensitive workflows

Risk mitigation:
- vLLM server failure → fallback to Ollama (slower, CPU-only)
- GPU memory overflow → implement document chunking
- Model drift → periodic accuracy benchmarking with known test sets
