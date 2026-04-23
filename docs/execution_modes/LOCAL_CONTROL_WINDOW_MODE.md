# Local Control Window Mode

## Purpose

Use this mode when the local stack is performing a control-window style audit, review, or truth check without defaulting to a remote control tool.

## Best use cases

- local truth verification
- completion challenge / acceptance review
- blocker-chain review
- framework-first decomposition for complex local tasks before Aider execution
- read-heavy repo audit work

## Not for

- broad unbounded implementation
- accepting narrative completion without evidence
- replacing canonical truth with local impressions

## Required reads

1. `docs/governance/CURRENT_OPERATING_CONTEXT.md`
2. `docs/roadmap/ROADMAP_AUTHORITY.md`
3. relevant canonical item YAML
4. relevant derived planning/dependency surfaces
5. relevant artifacts / validator outputs

## Operating rules

- be strict and evidence-first
- use local heavy-tier planning only to produce bounded execution packets or truth decisions
- do not over-credit partial progress
- if contradiction is found, either reject acceptance or hand off a bounded repair packet

## Expected outputs

- exact truth decision
- exact contradictions or confirmations found
- exact bounded repair packet if follow-on execution is required

## Stop conditions

Stop when:
- the truth decision is evidence-backed, or
- a bounded repair packet has been produced for execution
