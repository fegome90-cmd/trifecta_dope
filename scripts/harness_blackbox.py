#!/usr/bin/env python3
"""
Black-box CLI harness extension for Trifecta.
Wraps agent_harness_fp.sh and extracts PD_REPORT + Error Cards.
"""

import subprocess
import json
import re
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional


def parse_chunk_id_kind(chunk_id: str) -> str:
    """Extract kind from chunk ID (e.g., 'prime:abc' -> 'prime')."""
    if ":" in chunk_id:
        return chunk_id.split(":")[0].lower()
    return "unknown"


def build_ids_args(ids: list[str]) -> list[str]:
    """Build canonical --ids arguments.

    Single source of truth: comma-separated string.
    Returns: ["--ids", "id1,id2,id3"] or [] if empty
    """
    if not ids:
        return []
    return ["--ids", ",".join(ids)]


def resolve_ids(segment_path: str) -> Optional[list[str]]:
    """Resolve real chunk IDs from segment's context pack with deterministic ordering.

    Strategy:
    1. Try to load context_pack.json and extract IDs
    2. Sort by kind priority (prime=0, skill=1, doc=2, agent=3, unknown=9)
    3. If missing, run ctx sync first
    4. If still no IDs, return None (for error card handling)
    """
    context_pack_path = Path(segment_path) / "_ctx" / "context_pack.json"

    # Try loading existing pack
    if context_pack_path.exists():
        try:
            with open(context_pack_path) as f:
                pack = json.load(f)

            # Extract IDs from chunks
            chunks = pack.get("chunks", [])
            ids = [chunk["id"] for chunk in chunks if "id" in chunk]

            if len(ids) >= 2:
                return _sort_ids_deterministic(ids)[:2]
        except (json.JSONDecodeError, KeyError):
            pass  # Fall through to sync

    # Context pack missing or insufficient - run sync
    print("⚙️  Context pack missing or incomplete. Running ctx sync...")
    result = subprocess.run(
        ["uv", "run", "trifecta", "ctx", "sync", "-s", segment_path],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        return None  # Signal failure for error card

    # Try loading again after sync
    if context_pack_path.exists():
        try:
            with open(context_pack_path) as f:
                pack = json.load(f)
            chunks = pack.get("chunks", [])
            ids = [chunk["id"] for chunk in chunks if "id" in chunk]

            if len(ids) >= 2:
                return _sort_ids_deterministic(ids)[:2]
        except (json.JSONDecodeError, KeyError):
            pass

    # Still no IDs - return None for error card
    return None


def _sort_ids_deterministic(ids: list[str]) -> list[str]:
    """Sort IDs by kind priority, then alphabetically."""
    kind_priority = {
        "prime": 0,
        "skill": 1,
        "doc": 2,
        "agent": 3,
        "unknown": 9,
    }

    def sort_key(chunk_id: str):
        kind = parse_chunk_id_kind(chunk_id)
        priority = kind_priority.get(kind, 9)
        return (priority, chunk_id)

    return sorted(ids, key=sort_key)


def parse_pd_report(line: str) -> dict:
    """Parse PD_REPORT line into dict with typed numeric fields."""
    metrics = {}
    numeric_keys = {
        "chunks_returned",
        "chunks_requested",
        "chars_returned_total",
        "strong_hit",
        "support",
    }

    for match in re.finditer(r"(\w+)=([\w.]+)", line):
        key = match.group(1)
        value = match.group(2)

        # Type numeric fields as int
        if key in numeric_keys:
            try:
                metrics[key] = int(value)
            except ValueError:
                # Keep original if parsing fails
                metrics[key] = value
                metrics["_parse_error"] = True
        else:
            metrics[key] = value

    return metrics


def extract_error_card(stderr: str) -> Optional[dict]:
    """Extract Error Card from stderr if present."""
    # Look for TRIFECTA_ERROR_CODE marker
    for line in stderr.split("\n"):
        if "TRIFECTA_ERROR_CODE:" in line:
            match = re.search(r"TRIFECTA_ERROR_CODE:\s*(\w+)", line)
            if match:
                code = match.group(1)
                # Try to extract CLASS and CAUSE
                class_match = re.search(r"CLASS:\s*(\w+)", stderr)
                cause_match = re.search(r"CAUSE:\s*(.+?)(?=NEXT|$)", stderr, re.DOTALL)

                return {
                    "code": code,
                    "class": class_match.group(1) if class_match else "Unknown",
                    "cause": cause_match.group(1).strip() if cause_match else "",
                }
    return None


def generate_error_prompt(cmd: list[str], returncode: int, error_card: dict) -> str:
    """Generate Error→Prompt for agent recovery."""
    code = error_card.get("code", "UNKNOWN")
    error_class = error_card.get("class", "Unknown")

    # Deterministic recovery steps based on error code
    if code == "SEGMENT_NOT_INITIALIZED":
        steps = [
            "Run: trifecta create -s <segment_path>",
            "Verify prime file was created: ls _ctx/prime_*.md",
            "Run: trifecta ctx sync -s <segment_path>",
        ]
    elif code == "PRIME_FILE_NOT_FOUND":
        steps = [
            "Check segment directory structure",
            "Run: trifecta refresh-prime -s <segment_path>",
            "Verify _ctx/prime_*.md exists",
        ]
    else:
        steps = [
            "Check command syntax and arguments",
            "Verify segment is initialized (trifecta create)",
            "Review error cause above for specific guidance",
        ]

    prompt = f"""❌ Command Failed: {" ".join(cmd)}

Exit Code: {returncode}
Error Class: {error_class}
Error Code: {code}

Cause:
{error_card.get("cause", "No additional details")}

Recovery Steps:
"""
    for i, step in enumerate(steps, 1):
        prompt += f"{i}. {step}\n"

    return prompt


def run_command_with_extraction(cmd: list[str], cwd: str = ".") -> dict:
    """Run CLI command and extract PD_REPORT + Error Cards."""
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=cwd,
    )

    output = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "command": " ".join(cmd),
        "returncode": result.returncode,
        "success": result.returncode == 0,
    }

    # Extract PD_REPORT (last line of stdout if present)
    if result.stdout:
        lines = [line for line in result.stdout.strip().split("\n") if line]
        if lines and lines[-1].startswith("PD_REPORT v="):
            output["pd_report"] = parse_pd_report(lines[-1])

    # Extract Error Card (from stderr on failure)
    if result.returncode != 0:
        error_card = extract_error_card(result.stderr + "\n" + result.stdout)
        if error_card:
            output["error_card"] = error_card
            output["error_prompt"] = generate_error_prompt(cmd, result.returncode, error_card)
        else:
            # Fallback: generic error info
            output["error_info"] = {
                "stderr_preview": result.stderr[:200] if result.stderr else "",
                "stdout_preview": result.stdout[:200] if result.stdout else "",
            }

    return output


def main():
    """Main entry point - run example scenarios."""
    segment = sys.argv[1] if len(sys.argv) > 1 else "."

    # Resolve real IDs from context pack
    real_ids = resolve_ids(segment)

    # Handle harness failure with error card
    if real_ids is None:
        error_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "command": "harness_resolve_ids",
            "returncode": 2,
            "success": False,
            "error_card": {
                "code": "HARNESS_NO_IDS",
                "class": "Precondition",
                "cause": f"No chunk IDs found in context pack for segment: {segment}",
            },
            "error_prompt": f"""❌ Harness Failed: ID Resolution

Error Code: HARNESS_NO_IDS
Error Class: Precondition

Cause:
No chunk IDs found in context pack after sync attempt.
Segment: {segment}

Recovery Steps:
1. Verify segment is initialized: trifecta create -s {segment}
2. Run: trifecta ctx sync -s {segment}
3. Verify context pack has chunks: cat {segment}/_ctx/context_pack.json | jq '.chunks | length'
""",
        }

        # Print error card to stdout
        print("=" * 70)
        print(error_entry["error_prompt"])
        print("=" * 70)

        # Save to JSONL
        output_file = Path(segment) / "_ctx" / "telemetry" / "harness_results.jsonl"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "a") as f:
            f.write(json.dumps(error_entry) + "\n")

        sys.exit(2)

    print(f"✅ Resolved IDs: {real_ids}")

    scenarios = [
        ["uv", "run", "trifecta", "--help"],
        ["uv", "run", "trifecta", "ctx", "sync", "-s", segment],
        ["uv", "run", "trifecta", "ctx", "search", "-s", segment, "-q", "context"],
        ["uv", "run", "trifecta", "ctx", "get", "-s", segment]
        + build_ids_args(real_ids)
        + ["--pd-report"],
    ]

    results = []
    for cmd in scenarios:
        print(f"▶️  Running: {' '.join(cmd)}")
        result = run_command_with_extraction(cmd, cwd=segment)
        results.append(result)

        if result["success"]:
            print("   ✅ Success")
            if "pd_report" in result:
                print(f"   📊 PD_REPORT: {result['pd_report']}")
        else:
            print(f"   ❌ Failed (code {result['returncode']})")
            if "error_card" in result:
                print(f"   🔴 Error: {result['error_card']['code']}")
        print()

    # Save to JSONL
    output_file = Path(segment) / "_ctx" / "telemetry" / "harness_results.jsonl"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "a") as f:
        for result in results:
            f.write(json.dumps(result) + "\n")

    print(f"📝 Results saved to: {output_file}")
    print(f"📊 Total runs: {len(results)}")
    print(f"✅ Successful: {sum(1 for r in results if r['success'])}")
    print(f"❌ Failed: {sum(1 for r in results if not r['success'])}")


if __name__ == "__main__":
    main()
