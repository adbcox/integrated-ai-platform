# Aider prompt conventions

These conventions came out of the D-17-111 regression work. They are aimed at keeping Aider in SEARCH/REPLACE mode instead of drifting into narration, URL scraping, or wrong-target edits.

## 1. Disambiguate with structure, not line numbers

Prefer:
- `Replace the bare except inside function execute() with a specific exception tuple.`
- `Update the return path inside the if executor_log.exists() block.`

Avoid:
- `Replace the bare except at line 114.`
- `Fix the clause on line 87.`

Line numbers often destabilize SEARCH/REPLACE formatting and can make the model treat the number as text to match instead of edit guidance.

## 2. State intent plus before/after pattern

Prefer:
- `Change bare except: to except (json.JSONDecodeError, OSError):`
- `Add a docstring to the function that validates the executor log.`

The model needs the edit shape, not only the target.

## 3. Use scope qualifiers when a file has repeated patterns

Prefer:
- `Replace the first bare except in the executor block.`
- `Change all bare pass statements in the parser helpers.`

When a file has multiple matching clauses, mention the enclosing function, block, or unique nearby code.

## 4. Do not rely on line numbers

If a prompt includes `at line N` or `on line N`, the wrapper will warn. Use `--strip-line-refs` if you want the wrapper to remove those hints before Aider runs.

## 5. Route by task complexity, not just file size

Mechanical edits stay Tier 1 when the target is structurally clear, even on moderately sized files.

Inference-heavy edits move to Tier 2 when the prompt requires the model to infer the correct target from repeated patterns, hidden context, or subtle scope distinctions.

## 6. Use `--allow-ambiguous` only when you are deliberately testing the guard

The Layer 0 ambiguity guard blocks prompts like `replace the bare except clauses` when a file has multiple `except` clauses and no structural disambiguator. That block is intentional.

## 7. F25 standing instruction

F25 is the standing prompt-hygiene rule for future sessions:
- keep prompts concise and structural
- avoid URL-bearing context unless the task needs it
- avoid line numbers as target selectors
- prefer explicit scope qualifiers over vague references

## Examples from the D-17-111 failure

- Bad: `Replace the bare except clause at line 114 with specific exception types.`
- Good: `Replace the bare except inside the `if executor_log.exists()` block with `except (json.JSONDecodeError, OSError):`.`
- Bad: `Fix the except in this file.`
- Good: `Fix the bare `except:` in `test_stage3_with_executor()` only.`
