#!/usr/bin/env python3
"""Patch aider installation to disable all interactive prompts."""
import sys
import subprocess
from pathlib import Path

# Find aider installation
result = subprocess.run(["which", "aider"], capture_output=True, text=True)
aider_bin = result.stdout.strip()

if not aider_bin:
    print("❌ aider not found in PATH")
    sys.exit(1)

aider_path = Path(aider_bin).resolve().parent.parent / "lib"
print(f"🔍 Searching for aider library in: {aider_path}")

# Find main.py
main_files = list(aider_path.rglob("main.py"))
if not main_files:
    print(f"⚠️  No main.py found in {aider_path}")
    print("   Trying package installation path...")
    try:
        import aider
        aider_package = Path(aider.__file__).parent
        main_files = list(aider_package.parent.rglob("main.py"))
    except ImportError:
        print("❌ Could not locate aider package")
        sys.exit(1)

if not main_files:
    print("❌ Could not find aider/main.py")
    sys.exit(1)

for main_file in main_files:
    if "aider" not in str(main_file):
        continue

    print(f"✏️  Patching: {main_file}")
    content = main_file.read_text()
    original = content

    # Disable model warnings check
    content = content.replace(
        'if not self.args.no_show_model_warnings:',
        'if False:  # PATCHED: Never show warnings'
    )

    # Disable ask_yes_no prompts
    if 'def ask_yes_no(' in content:
        content = content.replace(
            'def ask_yes_no(',
            'def ask_yes_no_DISABLED('
        )

    # Disable update checks
    content = content.replace(
        'if self.args.check_update:',
        'if False:  # PATCHED: Disable update checks'
    )

    if content != original:
        main_file.write_text(content)
        print(f"✅ Patched {main_file.name}")
    else:
        print(f"⚠️  No patches applied to {main_file.name}")

print("\n✅ Aider patching complete")
