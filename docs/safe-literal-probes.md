# Safe Literal Probe Helper

Use this helper whenever you want to stay inside the proven fast micro lane (anchored literal wording/comment replacements in a single shell/bin file).

## Quick steps

1. Copy the template to a scratch message file:
   ```sh
   cp templates/safe-literal-probe-template.msg /tmp/probe_literal.msg
   ```
2. Edit the message so it anchors the exact file + literal you want to touch. Every message should:
   - name the file using `path/to/file.sh::short anchor`
   - say `replace exact text 'old' with 'new'` (or `update comment`, etc.)
   - end with `only. one replacement only. no behavior change.` unless you have a more precise literal note
3. Run the micro helper, pointing it at the message file and exactly one target file:
   ```sh
   make aider-micro-safe \
     AIDER_MICRO_MESSAGE_FILE=/tmp/probe_literal.msg \
     AIDER_MICRO_FILES="bin/quick_check.sh"
   ```

## Example

```
bin/quick_check.sh::status text replace exact text "echo \"[quick] Detecting changed files...\"" with "echo \"[quick] Checking for changed files...\"" only. one replacement only. no behavior change.
```

Pair every literal probe with an immediate `git status` + commit (or rollback) before launching the next probe.
