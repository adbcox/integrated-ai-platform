# Known Failures & Corrections

Common failure patterns and how to resolve them.

## YAML Parsing Errors

**Symptom**: `yaml.scanner.ScannerError` or `yaml.parser.ParserError`

**Common Causes**:
- Indentation error (YAML requires 2-space indentation)
- Missing colon after key
- Unquoted special characters

**Correction**:
1. Check indentation is exactly 2 spaces per level
2. Verify all keys end with `:` (colon)
3. Quote strings containing `#`, `&`, `*`, `{`, `}`, `[`, `]`
4. Test with: `python3 -c "import yaml; yaml.safe_load(open('file.yaml'))"`

## Cross-Reference Failures

**Symptom**: `KeyError` or `AssertionError` on ID validation

**Common Causes**:
- Roadmap item ID in sync_state.yaml doesn't exist in registry.yaml
- File path in execution pack doesn't actually exist
- Dependency reference to non-existent roadmap item

**Correction**:
1. Verify RM-* ID appears in both roadmap_registry.yaml and sync_state.yaml
2. Run: `grep "id:" docs/roadmap/items/*.yaml | cut -d: -f2 | sort | uniq`
3. Compare against roadmap_registry.yaml items list
4. Verify all file paths exist before referencing them

## Artifact Missing Errors

**Symptom**: Expected artifact not found after execution

**Common Causes**:
- File created but not in expected_artifacts list
- File created in wrong directory
- File created but validation failed before completion

**Correction**:
1. Check expected_artifacts list matches files actually created
2. Verify artifact_root directory exists
3. Confirm rollback didn't delete expected artifacts
4. List all files matching pattern: `find artifacts/ -type f -name "*.json" | head -10`

## Forbidden File Modifications

**Symptom**: Error "file modified outside allowed_files"

**Common Causes**:
- Accidentally modified tests/, framework/, or .github/
- Editing wrong version of a file
- Copy-paste error included forbidden path

**Correction**:
1. Check allowed_files list in execution control template
2. Verify no edits to files matching forbidden_files patterns
3. Git diff to see all changes: `git diff --name-only`
4. Revert any changes to forbidden files immediately
5. Re-apply only changes to allowed_files

## Syntax Validation Failures

**Symptom**: `make check` or `make quick` returns non-zero

**Common Causes**:
- Python syntax error in new .py file
- Unclosed parenthesis or quote
- Missing colon on if/for/def/class
- Whitespace error in YAML

**Correction**:
1. Run individual file check: `python3 -m py_compile <file.py>`
2. For YAML: `python3 -c "import yaml; yaml.safe_load(open('file.yaml'))"`
3. Check indentation and closing brackets
4. Run again: `make check`

## Git Status Failures

**Symptom**: Uncommitted changes prevent next operation

**Causes**:
- Artifact writes during execution
- Configuration file changes

**Correction**:
1. Review git status: `git status`
2. Verify only expected files are modified
3. If modifications are correct, commit them: `git add <files>; git commit -m "message"`
4. If incorrect, revert: `git checkout -- <files>`
