# Target Selection Policy

## Purpose

This document defines how the AI should rank and select the next roadmap task during autonomous or semi-autonomous operation.

## Primary rule

The AI must prefer the **highest-value eligible task** that most improves the architecture, governance, or active strategic cluster without violating readiness or dependency rules.

## Selection order

Rank candidates in this order:

1. architecture-critical active-cluster items
2. governance items that materially improve future autonomous pull quality
3. operational evidence and recovery items
4. inventory/capability items that materially improve planning intelligence
5. secondary branch-expansion items

## Eligibility filters

A task is not eligible for autonomous pull if:

- it lacks a normalized per-item file
- it is below the maturity needed for bounded execution
- it is blocked by unresolved dependencies
- it depends on undocumented external integrations
- it would force the AI to invent scope or title recovery
- it violates architecture sequence rules

## Tie-breakers

When two items have similar value, prefer the one that:

- reduces future planning or execution ambiguity
- unlocks multiple later tasks
- has fewer unresolved dependencies
- has clearer validation/closeout conditions
- reduces repeated-touch cost through grouped execution

## Anti-patterns

Do not prefer a task only because:

- it sounds interesting
- it is broad or flashy
- it creates a new branch before substrate maturity
- it has a vague title but no execution shape

## Reader shorthand

Pull the best governed task, not the most exciting one.
