from typing import Any
import subprocess

def audit_family_purity(allowed_new_files: Any, repo_root: Any) -> dict[str, Any]:
    if not isinstance(allowed_new_files, list) or not isinstance(repo_root, str):
        return {"purity_status": "invalid_input"}
    try:
        result = subprocess.run(
            ["git", "-C", repo_root, "status", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        lines = [l for l in result.stdout.strip().splitlines() if l.strip()]
    except Exception:
        return {"purity_status": "invalid_input"}
    allowed_set = set(allowed_new_files)
    unexpected = []
    untracked_count = 0
    for line in lines:
        code = line[:2]
        path = line[3:].strip()
        if code == "??":
            if path in allowed_set:
                untracked_count += 1
            else:
                unexpected.append(line)
        else:
            unexpected.append(line)
    if unexpected or untracked_count != len(allowed_new_files):
        return {
            "purity_status": "failed",
            "unexpected_entries": unexpected,
            "file_count": len(lines),
            "allowed_count": len(allowed_new_files),
        }
    return {
        "purity_status": "passed",
        "file_count": untracked_count,
        "allowed_count": len(allowed_new_files),
    }

