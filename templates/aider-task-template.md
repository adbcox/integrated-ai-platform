{
  "task": {
    "name": "<task-name>",
    "class": "<task-class>"
  },
  "objective": "<exact change in one sentence>",
  "target_files": [
    {"path": "path/to/file", "action": "modify"}
  ],
  "out_of_scope": [
    "files or behaviors Aider must not touch"
  ],
  "constraints": [
    "policy, style, or performance limits"
  ],
  "acceptance_criteria": [
    "observable outcome or diff expectation"
  ],
  "validation_commands": [
    "make quick"
  ],
  "limits": {
    "max_files": 3,
    "max_loc": 150,
    "max_roots": 1,
    "allowed_extra_globs": ["tests/**"],
    "forbidden_globs": ["config/**", "systemd/**", "secrets/**", "policies/**"]
  }
}
