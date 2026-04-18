from typing import Any

def audit_family_purity(allowed_new_files, repo_root):
    if not allowed_new_files or not repo_root or not isinstance(allowed_new_files, list) or not isinstance(repo_root, str):
        return {
            "family_purity_audit_status": "invalid_input",
            "file_count": 0,
            "allowed_count": 0
        }

    import subprocess
    try:
        status_output = subprocess.check_output(['git', '-C', repo_root, 'status', '--porcelain']).decode('utf-8')
        lines = status_output.splitlines()
        untracked_files = [line[3:] for line in lines if line.startswith('??')]
        modified_or_other = [l for l in lines if not l.startswith('??')]

        if modified_or_other:
            return {
                "family_purity_audit_status": "failed",
                "file_count": len(untracked_files),
                "allowed_count": len(allowed_new_files)
            }

        if set(untracked_files) == set(allowed_new_files):
            return {
                "family_purity_audit_status": "clean",
                "file_count": len(untracked_files),
                "allowed_count": len(allowed_new_files)
            }
        else:
            return {
                "family_purity_audit_status": "failed",
                "file_count": len(untracked_files),
                "allowed_count": len(allowed_new_files)
            }
    except Exception:
        return {
            "family_purity_audit_status": "invalid_input",
            "file_count": 0,
            "allowed_count": len(allowed_new_files) if allowed_new_files else 0
        }
