# Self-hosted Photo/Video Enhancement Stack Plan

## Goal
Map each named repo into a governed control-plane enhancement stack so the existing Real-ESRGAN scaffolding becomes a broader self-hosted plan that includes face restoration, video orchestration, and optional experimentation.

## Architecture split & pipeline
- **Media execution branch** owns end-to-end enhancement: job modeling, engine manifest, diagnostics, readiness, outputs, and linked provenance.
- **General enhancement stage**: Real-ESRGAN retains its role as the primary engine of record for upscaling, denoising, detail restoration, and working with image/video stills.
- **Face-restoration companion stage**: GFPGAN runs after Real-ESRGAN (or on its own where fine-grained face detail matters) to keep restored faces crisp while preserving provenance back to the original backup media.
- **Video orchestration**: Video2X (preferred) or REAL-Video-Enhancer wrap Real-ESRGAN/ GFPGAN runs through frame extraction + batch processing, with a manifest that tracks frame-level inputs/outputs, expected scale, and blocking readiness.
- **Experimental lab tooling**: chaiNNer is documented as a non-core lab tool that can assist with stylized denoising or alternative filters for research pilots without affecting the core job path.

Pipeline flow (per media item):
1. Pull backup handoff asset (image or video) into `media_execution_jobs`.
2. Record enhancement job targeting Real-ESRGAN (5×/4×/denoise) with metadata about operation, engine family, and readiness.
3. Real-ESRGAN processes still frames; optional GFPGAN stage attaches face-restoration artifacts.
4. For video sources, Video2X or REAL-Video-Enhancer orchestrate chunking/frame extraction + Real-ESRGAN/GFPGAN invocations, writing diagnostics to a per-video manifest.
5. chaiNNer remains documented as a lab job (with `media_enhancement_jobs.experimental=true`) whose outputs remain isolated until reviewed.

## Repo-specific placement

### Real-ESRGAN
- **Role**: Primary general enhancement engine (upscale, denoise, detail recovery).
- **Branch owner**: `media_execution` + `media_enhancement_jobs`/`outputs` artifacts.
- **Timing**: Near-term, core.
- **Artifacts**: `media_enhancement_jobs.json`, `media_enhancement_outputs.json`, `media_enhancement_engine_manifest.json` entries referencing the Real-ESRGAN build, plus diagnostics/readiness records per operation.
- **Governance risks**: Need to ensure provenance tracks original handoff ID and job chain (with face restoration stage); treat outputs as advisory until review.
- **Why useful**: Mirrors paid-model image enhancement by using a battle-tested open-source engine with GPU-local inference.
- **Limits**: No multimodal reasoning; video coverage requires orchestration by Video2X/REAL-Video-Enhancer.

### GFPGAN
- **Role**: Face-restoration companion stage invoked after (or alongside) Real-ESRGAN when faces are present.
- **Branch owner**: `media_execution` as a secondary stage, with `media_face_restoration_jobs` or by tagging enhancement jobs with `face_restoration=true`.
- **Timing**: Near-term, semi-core companion.
- **Artifacts**: Additional outputs referencing GFPGAN, `provenance_summary` noting face focus, optional `media_face_restoration_jobs.json`.
- **Governance**: Face-focused stage must preserve review history to avoid identity assertions—only mention face quality improvements, not recognition.
- **Why useful**: Keeps faces natural post-enhancement and softens artifacts, giving the feel of premium portrait enhancement in paid tools.
- **Limits**: Avoid pipelines that feed GFPGAN into identity claims; treat as purely visual.

### Video2X (preferred video orchestration)
- **Role**: Video orchestration wrapper that extracts frames, runs Real-ESRGAN/GFPGAN, and reassembles clips.
- **Branch owner**: `media_execution` with optional `media_video_pipeline_manifest.json` describing frame batches, rate, and blocking reasons.
- **Timing**: Mid-term, core for video processing.
- **Artifacts**: `media_video_pipeline_manifest.json`, `media_execution_jobs` entries for each frame group, diagnostics on frame extraction.
- **Governance**: Must track clip provenance (source event, frame IDs) and note blocking conditions (missing GPU, high load).
- **Why useful**: Provides paid-tool-like video enhancement by automating frame-level Real-ESRGAN runs while remaining orchestrated.
- **Limits**: Resource heavy; keep initial pilots small and require manual review before reassembly.

### REAL-Video-Enhancer (alternative video orchestration)
- **Role**: Optional/parallel wrapper similar to Video2X; consider if Video2X integration falls short.
- **Branch owner**: `media_execution` as an alternate pipeline visible via configuration.
- **Timing**: Mid-term, optional fallback.
- **Artifacts**: Manifest entries linking to REAL-Video-Enhancer-specific config, plus cross-reference to Real-ESRGAN jobs.
- **Governance**: Only enable after Video2X stabilized; avoid splitting resources across multiple orchestration layers.
- **Why useful**: Offers different upscaling/noise patterns if needed later.
- **Limits**: Avoid dual pipeline sprawl until Video2X is proven; treat as experimental until then.

### chaiNNer
- **Role**: Experimental/lab denoising/refinement tool for unusual creative enhancements.
- **Branch owner**: `media_execution.experimental` or a new `media_enhancement_experiments.json` manifest.
- **Timing**: Later, experimental.
- **Artifacts**: Mark jobs/outputs as `experimental=true`, include readiness notes to remind operators of manual review requirements.
- **Governance**: Keep clearly flagged, no automation, no integration into production dashboards perhaps except a lab log; treat as knowledge capture only.
- **Why useful**: Provides a sandbox for trying stylized flows without impacting the core stack.
- **Limits**: No throughput guarantee; should never feed into privacy evidence without explicit review.

## Artifact model
- Continue using `media_execution_jobs.json`, `media_enhancement_outputs.json`, `media_enhancement_engine_manifest.json` and the readiness/diagnostics artifacts already introduced.
- Add `media_video_pipeline_manifest.json` capturing block status, frame counts, video source IDs, and links to Real-ESRGAN/GFPGAN jobs.
- Consider `media_face_restoration_jobs.json` or job tagging to show GFPGAN usage.
- Ensure `media_enhancement_execution_readiness.json` reflects Real-ESRGAN job readiness and video orchestration blockers.
- Document experimental runs (chaiNNer) separately to avoid confusion.

## Provenance & discovery
- Each artifact must link back to `backup_media_handoff.json` IDs and `media_execution_manifest.json` entries.
- search_index should expose `media_video_pipeline_manifest` rows along with job IDs so operators can query video-specific enhancements.
- Dashboard surfaces should include:
  - Enhancement engine view listing Real-ESRGAN jobs, GFPGAN follow-ups, video pipeline manifests, and readiness status.
  - Video enhancement detail page showing frame counts, orchestration gaps, and output placeholders.
  - Experimental lab panel for chaiNNer with warnings.

## Phased plan & priority order
1. **Real-ESRGAN general enhancement** (already scaffolded) — finalize manifest/readiness metadata.
2. **GFPGAN companion stage** — record outputs, ensure face provenance, add face-job artifact.
3. **Video2X orchestration** — add pipeline manifest and link to Real-ESRGAN jobs; treat sanity tests as gating.
4. **REAL-Video-Enhancer fallback** — document as optional, only implement if Video2X gaps appear.
5. **chaiNNer experimentation** — keep as lab log, no dashboard integration until proven.
- **Next implementation priority**: Complete GFPGAN companion stage so face restoration jobs are recorded with Real-ESRGAN operations, keeping the enhancement stack cohesive before expanding video orchestration.

## Risks & exclusions
- **Sprawl**: Limit orchestration to Video2X first; avoid supporting multiple heavy wrappers simultaneously.
- **Face misuse**: GFPGAN outputs are purely visual; never interface them with recognition/evidence materials without manual review.
- **Experimental blur**: chaiNNer runs remain isolated to lab logs and never feed into automated pipelines.
- **Scaling**: Track GPU readiness via `media_enhancement_execution_readiness.json` to avoid queuing blocked jobs.

## Summary and next steps
- The doc adds Real-ESRGAN, GFPGAN, Video2X, REAL-Video-Enhancer, and chaiNNer to the enhancement plan.
- Next implementation priority: capture GFPGAN companion stage metadata and integrate it with existing Real-ESRGAN jobs.
