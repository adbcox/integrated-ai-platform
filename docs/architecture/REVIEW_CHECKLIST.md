# Architecture Review Checklist

## Purpose

Use this checklist when reviewing a new roadmap item, architecture change, branch proposal, or external-system adoption decision.

## Checklist

- Does this respect the shared runtime substrate rule?
- Does this preserve Ollama-first as the default routine coding posture?
- Does this avoid creating a new backbone service or branch-owned execution loop?
- Does this align with the current phase model?
- Does it improve or at least not undermine artifact and validation consistency?
- Are authority surfaces still clear after the change?
- If external software is involved, is it cataloged in the external applications registry?
- If a new domain branch is involved, does it specialize without forking the platform?
- Are roadmap impacts and affected systems/file families clear?
- Does the canonical architecture set need to be updated in the same change?

## Reader shorthand

If several answers are unclear or negative, the change probably needs architectural revision before execution.
