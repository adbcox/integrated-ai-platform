# Media Enhancement Reuse Register

## Purpose

This document defines the reuse-first adoption posture for media enhancement, restoration, interpolation, tagging, and searchable media workflows.

This is separate from Plex and Arr acquisition automation.
It covers enhancement and post-processing pipelines for images and video.

## Core rule

For media enhancement:
- prefer complete, runnable pipelines when they already solve extraction, enhancement, muxing, and resume logic well
- prefer portable binaries or Dockerized tools when dependency complexity is high
- prefer thin orchestration wrappers over rebuilding FFmpeg, frame-splitting, audio-remux, or model-management logic from scratch
- prefer existing tagging and searchable-gallery tools over writing weak first-pass media AI search systems

## Enhancement reuse register

| System or repo | Role | Reuse mode | What to reuse | Notes |
|---|---|---|---|---|
| Video2X | automated video enhancement pipeline | adopt-selective and wrap | FFmpeg orchestration, frame pipeline, upscaling lifecycle, batch processing | Strong full pipeline reference and tool |
| REAL Video Enhancer | cross-platform video enhancement app | adopt-selective and reference | interpolation, upscaling, denoise, backend compatibility posture | Strong practical app and implementation reference |
| Upscayl | image enhancement desktop app | adopt-selective and reference | UX patterns, packaging, drag-and-drop, local image upscaling workflow | Strong UI and packaging reference |
| Real-ESRGAN binaries and scripts | image and video upscaling core | hybrid and reuse | portable binaries, inference scripts, direct subprocess integration | Strong low-friction enhancement engine |
| CodeFormer | face restoration | hybrid and reuse | face alignment, crop, restore, paste-back logic | Strong face restoration component |
| GFPGAN | face restoration | hybrid and reuse | face restoration stage in broader pipelines | Strong face enhancement component |
| Flowframes | frame interpolation reference | reference-only selective | resume-state and interpolation workflow ideas | Useful interpolation reference |
| waifu2x-extension-gui | backend compatibility reference | reference-only selective | cross-hardware support ideas and processing options | Useful portability reference |
| pratik227/upscale_video_4k or similar scripts | Python enhancement wrapper reference | reference-only selective | audio remux, hardware detection, simple local-first video pipeline patterns | Strong lightweight script reference |
| willermo/video-enhancer or similar | two-stage restoration pipeline reference | reference-only selective | Real-ESRGAN plus GFPGAN chaining ideas | Good simple restoration pattern |
| ultralytics YOLO | object tagging and indexing | reuse as library | detection, labels, confidence, lightweight searchable metadata generation | Primary tagging engine candidate |
| ImageAI | simple detection wrapper | selective library reuse | easier object detection wrappers for image and video | Simpler but less central than Ultralytics |
| FiftyOne | media indexing and visual search tooling | adopt-selective and wrap | local visualization, filtering, tag and confidence inspection | Strong searchable media workbench |
| DeepStack | self-hosted vision API | conditional | detection as local API service | Candidate if API-first architecture is preferred |
| LibrePhotos | self-hosted photo search and management | adopt-selective and reference | AI photo tagging and searchable management patterns | Strong finished product reference |
| PhotoPrism | self-hosted photo management | adopt-selective and reference | AI-powered search and gallery patterns | Strong finished product reference |
| Immich | self-hosted backup and gallery | adopt-selective and reference | mobile-first search and backup patterns | Strong product and UX reference |

## Preferred ownership by role

### A. Video enhancement pipeline
Primary current candidates:
- Video2X
- REAL Video Enhancer

### B. Image enhancement pipeline
Primary current candidates:
- Real-ESRGAN
- CodeFormer
- GFPGAN
- Upscayl as reference app or selective desktop tool

### C. Object tagging and indexing
Primary current candidate:
- Ultralytics YOLO

### D. Searchable media workbench
Primary current candidates:
- FiftyOne
- LibrePhotos
- PhotoPrism
- Immich as product reference

## Assistant rules

1. Do not rebuild frame extraction, audio muxing, resume logic, or hardware detection first.
2. Prefer Dockerized or binary-backed tools where dependency weight is high.
3. Use model components only where custom orchestration is actually needed.
4. Keep enhancement and searchable-media work separate from Plex and Arr acquisition automation.
5. Choose one primary tool per role before broadening into overlapping products.

## Recommended first-wave media enhancement reuse targets

1. Video2X
2. REAL Video Enhancer
3. Real-ESRGAN plus CodeFormer or GFPGAN component chain
4. Ultralytics YOLO
5. FiftyOne or one product-level searchable media reference

## Relationship to roadmap

This document is especially relevant to:
- RM-MEDIA-003
- RM-GOV-009
- RM-OPS-006

## Notes

This register is intended to make the media enhancement branch reuse-first by default.