# Media Reuse Implementation Wave

## Purpose

This document defines the first concrete reuse-first implementation wave for the media automation branch.

It exists to convert media-stack research into a bounded execution packet so assistants install, wrap, or lightly modify mature OSS systems instead of recreating broad media automation logic.

## Scope of this wave

Included now:
- PyArr
- PlexAPI
- Overseerr
- Maintainerr
- Kometa
- one watchlist-sync evaluation lane

Selective references only in this wave:
- Homarr
- Plex Autoscan
- syncarr

Deferred from this wave:
- custom full media portal from scratch
- custom metadata engine from scratch
- custom request portal from scratch
- custom cleanup rule engine from scratch
- broad multi-instance routing engine

## Wave goals

1. improve direct Plex and Arr automation with standard Python libraries
2. adopt mature request, maintenance, and metadata systems instead of rebuilding them
3. choose one primary watchlist-sync pattern rather than inventing custom sync first
4. leave the media branch with repo-visible reuse guidance and bounded implementation posture

## Wave inventory

### 1. PyArr
- role: low-level Arr automation library
- posture: reuse as library
- outputs required: install method, wrapper boundary, validation sample commands, rollback notes

### 2. PlexAPI
- role: low-level Plex automation library
- posture: reuse as library
- outputs required: install method, wrapper boundary, validation sample commands, rollback notes

### 3. Overseerr
- role: request portal and discovery UX
- posture: adopt-selective and wrap
- outputs required: deployment posture, integration boundary, validation path, rollback notes

### 4. Maintainerr
- role: maintenance and cleanup rules
- posture: adopt-selective and wrap
- outputs required: deployment posture, rule-engine integration boundary, validation path, rollback notes

### 5. Kometa
- role: metadata, collections, overlays
- posture: adopt-selective and wrap
- outputs required: deployment posture, config boundary, validation path, rollback notes

### 6. Watchlist-sync lane
Choose one primary pattern to evaluate first from:
- Fetcharr
- Watchlistarr
- Pulsarr

Outputs required:
- comparison note
- primary candidate recommendation
- reasons for not adopting the others first
- validation path

## Governing rules

- all adopted media systems remain subordinate to canonical roadmap and validation truth
- do not build custom broad media subsystems if the selected products already own the role well
- use libraries for custom glue logic only where necessary
- do not adopt multiple products as co-primary owners of the same role without explicit reason

## Validation contract

The wave is only materially complete when:
- each selected system has a clear role and owner
- each selected system has install or wrap guidance
- each selected system has validation steps
- assistants no longer need to rethink whether to build these media subsystems from scratch

## Relationship to roadmap

Primary owner:
- RM-MEDIA-001

Secondary relevance:
- RM-GOV-009
- RM-OPS-006

## Notes

This packet is the media-side equivalent of the reuse-first implementation wave for local AI coding.