import os
import re
from pathlib import Path

# Patterns to match
USER_HOME = "<REPO_ROOT>"
REPLACEMENT = "<REPO_ROOT>"

# Files to scrub (glob patterns)
SCRUB_TARGETS = [
    "openspec/changes/**/*.md",
    "openspec/specs/**/*.md",
    "_ctx/logs/reconcile/*.log",
    "_ctx/logs/reconcile/*.patch",
    "README.md",
    "docs/*.md",
    "tests/fixtures/**/*.log",
    "tests/fixtures/**/*.patch",
    "tests/fixtures/**/*.json"
]

def scrub_file(file_path: Path):
    if not file_path.exists():
        return
    
    print(f"Scrubbing {file_path}...")
    content = file_path.read_text(encoding="utf-8")
    
    # Simple replacement for now, could be improved with regex
    new_content = content.replace(USER_HOME, REPLACEMENT)
    
    if new_content != content:
        file_path.write_text(new_content, encoding="utf-8")
        print(f"  Done.")
    else:
        print(f"  No matches found.")

def main():
    repo_root = Path(__file__).resolve().parents[1]
    os.chdir(repo_root)
    
    for pattern in SCRUB_TARGETS:
        for file_path in repo_root.glob(pattern):
            if file_path.is_file():
                scrub_file(file_path)

if __name__ == "__main__":
    main()
