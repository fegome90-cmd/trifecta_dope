#!/usr/bin/env python3
"""Task verifier for GAIA-lite benchmark.

Verifies task outputs against acceptance criteria using multiple verifier types:
- count_min: Minimum count of items
- regex_match: Pattern matching in output
- command: Shell command validation
- json_parse: Valid JSON output
"""

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


def verify_count_min(output: str, field: str, min_count: int) -> tuple[bool, str]:
    """Verify minimum count of items in output."""
    lines = [l.strip() for l in output.strip().split("\n") if l.strip()]
    count = len(lines)
    passed = count >= min_count
    return passed, f"{field}: {count} >= {min_count}"


def verify_regex_match(output: str, pattern: str) -> tuple[bool, str]:
    """Verify output contains pattern."""
    matches = re.findall(pattern, output)
    count = len(matches)
    passed = count > 0
    return passed, f"Pattern '{pattern}': {count} matches"


def verify_command(output: str, cmd: str, expected: Any, comparison: str = "equals") -> tuple[bool, str]:
    """Verify by running a shell command."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        actual = result.stdout.strip()
        
        if comparison == "equals":
            passed = str(actual) == str(expected)
            return passed, f"Command: expected '{expected}', got '{actual}'"
        elif comparison == "contains":
            passed = str(expected) in actual
            return passed, f"Command: '{expected}' in '{actual}'"
        else:
            return False, f"Unknown comparison: {comparison}"
    except Exception as e:
        return False, f"Command failed: {e}"


def verify_json_parse(output: str) -> tuple[bool, str]:
    """Verify output is valid JSON."""
    try:
        data = json.loads(output)
        return True, f"Valid JSON with {len(data)} top-level keys"
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON: {e}"


def verify_task(task: dict, output: str) -> dict:
    """Verify task output against verifiers.
    
    Returns:
        dict with: passed, score, details
    """
    verifiers = task.get("verifiers", [])
    results = []
    all_passed = True
    
    for v in verifiers:
        v_type = v.get("type")
        
        if v_type == "count_min":
            passed, detail = verify_count_min(
                output,
                v.get("field", "items"),
                v.get("min", 0)
            )
            results.append({"type": v_type, "passed": passed, "detail": detail})
            if not passed:
                all_passed = False
                
        elif v_type == "regex_match":
            passed, detail = verify_regex_match(
                output,
                v.get("pattern", "")
            )
            results.append({"type": v_type, "passed": passed, "detail": detail})
            if not passed:
                all_passed = False
                
        elif v_type == "command":
            passed, detail = verify_command(
                output,
                v.get("cmd", ""),
                v.get("expected", ""),
                v.get("comparison", "equals")
            )
            results.append({"type": v_type, "passed": passed, "detail": detail})
            if not passed:
                all_passed = False
                
        elif v_type == "json_parse":
            passed, detail = verify_json_parse(output)
            results.append({"type": v_type, "passed": passed, "detail": detail})
            if not passed:
                all_passed = False
    
    return {
        "passed": all_passed,
        "score": sum(1 for r in results if r["passed"]) / max(len(results), 1),
        "details": results,
    }


def main():
    if len(sys.argv) < 3:
        print("Usage: verify_task.py <task.json> <output.txt>")
        sys.exit(1)
    
    task_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])
    
    if not task_path.exists():
        print(f"Error: Task file not found: {task_path}")
        sys.exit(1)
    
    if not output_path.exists():
        print(f"Error: Output file not found: {output_path}")
        sys.exit(1)
    
    with open(task_path) as f:
        task = json.load(f)
    
    output = output_path.read_text()
    
    result = verify_task(task, output)
    
    print(json.dumps(result, indent=2))
    
    sys.exit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
