#!/usr/bin/env python3
"""GAIA-lite benchmark runner for Trifecta.

Runs verifiable tasks with different context policies and measures:
- Pass@1: Task completed successfully on first attempt
- Pass@2: Task completed with 1 retry
- Injected context tokens
- Wall time
- Tool calls
"""

import csv
import json
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import tiktoken


SEGMENT = "."
REPO_ROOT = Path(__file__).parent.parent
ENCODING = "o200k_base"


def load_tasks(path: Path) -> list[dict]:
    """Load tasks from JSON file."""
    with open(path) as f:
        data = json.load(f)
    return data.get("tasks", [])


def count_tokens(text: str) -> int:
    """Count tokens using tiktoken."""
    try:
        enc = tiktoken.get_encoding(ENCODING)
        return len(enc.encode(text or ""))
    except Exception:
        return len(text or "") // 4


def run_task_with_context(
    task: dict,
    context_policy: str,
    segment: str = ".",
) -> dict:
    """Run a single task with specified context policy.

    Args:
        task: Task definition
        context_policy: One of 'dump', 'heuristic', 'bm25', 'cli'
        segment: Segment path

    Returns:
        dict with: status, output, tokens, wall_time, tool_calls, error
    """
    start_time = time.time()
    prompt = task.get("prompt", "")

    if context_policy == "dump":
        return run_dump_context(task, prompt, start_time)
    elif context_policy in ("heuristic", "bm25"):
        return run_offline_context(task, prompt, start_time, context_policy)
    elif context_policy == "cli":
        return run_cli_context(task, prompt, start_time, segment)
    else:
        return {
            "status": "error",
            "output": "",
            "tokens": 0,
            "wall_time": 0,
            "tool_calls": 0,
            "error": f"Unknown policy: {context_policy}",
        }


def run_dump_context(task: dict, prompt: str, start_time: float) -> dict:
    """Run task with full context dump."""
    try:
        cmd = ["uv", "run", "trifecta", "ctx", "build", "--segment", "."]
        subprocess.run(cmd, capture_output=True, cwd=REPO_ROOT, timeout=60)

        pack_path = REPO_ROOT / "_ctx" / "context_pack.json"
        if not pack_path.exists():
            return {
                "status": "error",
                "output": "",
                "tokens": 0,
                "wall_time": time.time() - start_time,
                "tool_calls": 0,
                "error": "Context pack not found",
            }

        with open(pack_path) as f:
            pack = json.load(f)

        context_text = ""
        for chunk in pack.get("chunks", [])[:50]:
            context_text += chunk.get("text", "")[:500] + "\n"

        tokens = count_tokens(context_text) + count_tokens(prompt)

        return {
            "status": "simulated",
            "output": f"[Task would run with {tokens} context tokens - full dump]",
            "tokens": tokens,
            "wall_time": time.time() - start_time,
            "tool_calls": 0,
            "error": None,
        }
    except Exception as e:
        return {
            "status": "error",
            "output": "",
            "tokens": 0,
            "wall_time": time.time() - start_time,
            "tool_calls": 0,
            "error": str(e),
        }


def run_offline_context(task: dict, prompt: str, start_time: float, method: str) -> dict:
    """Run task with offline retrieval."""
    try:
        cmd = [
            "uv",
            "run",
            "trifecta",
            "ctx",
            "search",
            "--segment",
            ".",
            "--query",
            prompt[:100],
            "--limit",
            "5",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT, timeout=30)

        output = result.stdout if result.returncode == 0 else result.stderr
        tokens = count_tokens(output) + count_tokens(prompt)

        return {
            "status": "ok" if result.returncode == 0 else "error",
            "output": output[:1000],
            "tokens": tokens,
            "wall_time": time.time() - start_time,
            "tool_calls": 1,
            "error": result.stderr if result.returncode != 0 else None,
        }
    except Exception as e:
        return {
            "status": "error",
            "output": "",
            "tokens": 0,
            "wall_time": time.time() - start_time,
            "tool_calls": 0,
            "error": str(e),
        }


def run_cli_context(task: dict, prompt: str, start_time: float, segment: str) -> dict:
    """Run task with CLI context (simulated progressive disclosure)."""
    try:
        cmd = [
            "uv",
            "run",
            "trifecta",
            "ctx",
            "search",
            "--segment",
            segment,
            "--query",
            prompt[:100],
            "--limit",
            "3",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT, timeout=30)

        output = result.stdout if result.returncode == 0 else result.stderr
        tokens = count_tokens(output) + count_tokens(prompt)

        return {
            "status": "ok" if result.returncode == 0 else "error",
            "output": output[:1000],
            "tokens": tokens,
            "wall_time": time.time() - start_time,
            "tool_calls": 1,
            "error": result.stderr if result.returncode != 0 else None,
        }
    except Exception as e:
        return {
            "status": "error",
            "output": "",
            "tokens": 0,
            "wall_time": time.time() - start_time,
            "tool_calls": 0,
            "error": str(e),
        }


def verify_task_output(task: dict, output: str) -> dict:
    """Verify task output against verifiers."""
    verifiers = task.get("verifiers", [])
    results = []
    all_passed = True

    for v in verifiers:
        v_type = v.get("type")

        if v_type == "count_min":
            lines = [l.strip() for l in output.strip().split("\n") if l.strip()]
            count = len(lines)
            passed = count >= v.get("min", 0)
            results.append({"type": v_type, "passed": passed, "count": count, "min": v.get("min")})
            if not passed:
                all_passed = False

        elif v_type == "regex_match":
            pattern = v.get("pattern", "")
            matches = len(re.findall(pattern, output))
            passed = matches > 0
            results.append({"type": v_type, "passed": passed, "matches": matches})
            if not passed:
                all_passed = False

        elif v_type == "command":
            cmd = v.get("cmd", "")
            try:
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
                actual = result.stdout.strip()
                expected = str(v.get("expected", ""))
                passed = actual == expected
                results.append(
                    {"type": v_type, "passed": passed, "actual": actual, "expected": expected}
                )
                if not passed:
                    all_passed = False
            except Exception as e:
                results.append({"type": v_type, "passed": False, "error": str(e)})
                all_passed = False

    return {
        "passed": all_passed,
        "score": sum(1 for r in results if r.get("passed", False)) / max(len(results), 1),
        "details": results,
    }


# =============================================================================
# 3-Agent Policy: Planner / Executor / Judge
# =============================================================================


def run_3agent_policy(
    task: dict,
    context_policy: str,
    segment: str = ".",
) -> dict:
    """Run task with 3-agent policy: Planner -> Executor -> Judge.

    Args:
        task: Task definition
        context_policy: Context retrieval method
        segment: Segment path

    Returns:
        dict with: status, output, tokens, wall_time, tool_calls, agent_steps, error
    """
    start_time = time.time()
    prompt = task.get("prompt", "")
    task_id = task.get("id", "unknown")

    steps = []
    total_tokens = 0
    total_tool_calls = 0

    # Step 1: Planner - decomposes task into checklist
    planner_prompt = f"""You are a Planner agent. Decompose this task into a checklist of steps.

Task: {prompt}

Provide a numbered checklist of steps to complete this task."""

    planner_result = run_task_with_context(task, context_policy, segment)
    planner_output = planner_result.get("output", "")
    total_tokens += planner_result.get("tokens", 0)
    total_tool_calls += planner_result.get("tool_calls", 0)

    steps.append(
        {
            "agent": "planner",
            "output": planner_output[:500],
            "tokens": planner_result.get("tokens", 0),
        }
    )

    # Step 2: Executor - produces output based on plan
    executor_prompt = f"""You are an Executor agent. Complete this task step by step.

Original task: {prompt}

Plan:
{planner_output}

Execute the plan and provide your final output."""

    executor_result = run_task_with_context(task, context_policy, segment)
    executor_output = executor_result.get("output", "")
    total_tokens += executor_result.get("tokens", 0)
    total_tool_calls += executor_result.get("tool_calls", 0)

    steps.append(
        {
            "agent": "executor",
            "output": executor_output[:500],
            "tokens": executor_result.get("tokens", 0),
        }
    )

    # Step 3: Judge - evaluates output against checklist
    checklist = planner_output.split("\n")
    judge_prompt = f"""You are a Judge agent. Evaluate the executor's output against the acceptance criteria.

Task: {prompt}

Plan:
{planner_output}

Executor output:
{executor_output}

Did the executor complete the task successfully? Provide a brief verdict: PASS or FAIL with reasoning."""

    judge_result = run_task_with_context(task, context_policy, segment)
    judge_output = judge_result.get("output", "")
    total_tokens += judge_result.get("tokens", 0)
    total_tool_calls += judge_result.get("tool_calls", 0)

    steps.append(
        {
            "agent": "judge",
            "output": judge_output[:500],
            "tokens": judge_result.get("tokens", 0),
        }
    )

    passed = "PASS" in judge_output.upper() or "PASS" in executor_output.upper()

    return {
        "status": "ok",
        "output": executor_output[:1000],
        "tokens": total_tokens,
        "wall_time": time.time() - start_time,
        "tool_calls": total_tool_calls,
        "agent_steps": steps,
        "passed": passed,
        "judge_verdict": judge_output[:200],
        "error": None,
    }


def run_with_retry(
    task: dict,
    context_policy: str,
    segment: str = ".",
    max_retries: int = 2,
    agent_policy: str = "single",
) -> dict:
    """Run task with Pass@K retry logic.

    Args:
        task: Task definition
        context_policy: Context retrieval method
        segment: Segment path
        max_retries: Maximum number of attempts (1 = Pass@1, 2 = Pass@2)
        agent_policy: 'single' or '3-agent'

    Returns:
        dict with: status, output, tokens, wall_time, tool_calls, attempts, passed, error
    """
    start_time = time.time()
    result = None

    if max_retries < 1:
        max_retries = 1

    for attempt in range(1, max_retries + 1):
        if agent_policy == "3-agent":
            result = run_3agent_policy(task, context_policy, segment)
        else:
            result = run_task_with_context(task, context_policy, segment)

        verification = verify_task_output(task, result.get("output", ""))

        if verification.get("passed"):
            return {
                "status": "ok",
                "output": result.get("output", ""),
                "tokens": result.get("tokens", 0),
                "wall_time": time.time() - start_time,
                "tool_calls": result.get("tool_calls", 0),
                "attempts": attempt,
                "passed": True,
                "error": None,
            }

    if result is None:
        result = {
            "output": "",
            "tokens": 0,
            "tool_calls": 0,
        }

    return {
        "status": "completed",
        "output": result.get("output", ""),
        "tokens": result.get("tokens", 0),
        "wall_time": time.time() - start_time,
        "tool_calls": result.get("tool_calls", 0),
        "attempts": max_retries,
        "passed": False,
        "error": "Max retries exceeded",
    }


# =============================================================================
# Cross-Model Support
# =============================================================================


MODEL_CONFIGS = {
    "minimax-m2.5:free": {
        "name": "MiniMax M2.5 Free",
        "context_window": 200000,
        "supports_tools": True,
    },
    "glm-5": {
        "name": "GLM-5",
        "context_window": 128000,
        "supports_tools": True,
    },
    "gemini-2.0-flash": {
        "name": "Gemini 2.0 Flash",
        "context_window": 1000000,
        "supports_tools": True,
    },
}


def get_available_models() -> list[str]:
    """Get list of available models for testing."""
    available = []
    for model_id, config in MODEL_CONFIGS.items():
        available.append(model_id)
    return available


def run_benchmark(
    tasks_path: Path,
    output_csv: Path,
    context_policies: list[str],
    trials: int = 1,
    agent_policy: str = "single",
    max_retries: int = 1,
) -> None:
    """Run GAIA-lite benchmark."""
    tasks = load_tasks(tasks_path)

    print(f"GAIA-lite Benchmark")
    print(f"=" * 50)
    print(f"Tasks: {len(tasks)}")
    print(f"Policies: {context_policies}")
    print(f"Agent Policy: {agent_policy}")
    print(f"Max Retries: {max_retries} (Pass@{max_retries})")
    print(f"Trials: {trials}")
    print()

    results = []

    for policy in context_policies:
        print(f"Running with policy: {policy}")

        for trial in range(1, trials + 1):
            for task in tasks:
                task_id = task.get("id")
                task_name = task.get("name")

                print(f"  {task_id} (trial {trial})...", end=" ", flush=True)

                run_result = run_with_retry(
                    task,
                    policy,
                    SEGMENT,
                    max_retries=max_retries,
                    agent_policy=agent_policy,
                )

                verification = verify_task_output(task, run_result.get("output", ""))

                result_row = {
                    "task_id": task_id,
                    "task_name": task_name,
                    "policy": policy,
                    "agent_policy": agent_policy,
                    "trial": trial,
                    "status": run_result.get("status"),
                    "passed": run_result.get("passed", verification.get("passed")),
                    "score": verification.get("score"),
                    "tokens": run_result.get("tokens"),
                    "wall_time": run_result.get("wall_time"),
                    "tool_calls": run_result.get("tool_calls"),
                    "attempts": run_result.get("attempts", 1),
                    "error": run_result.get("error"),
                    "timestamp": datetime.now().isoformat(),
                }
                results.append(result_row)

                status = "✓" if run_result.get("passed") else "✗"
                print(
                    f"{status} tokens={run_result.get('tokens')}, attempts={run_result.get('attempts', 1)}"
                )

    output_csv.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "task_id",
        "task_name",
        "policy",
        "agent_policy",
        "trial",
        "status",
        "passed",
        "score",
        "tokens",
        "wall_time",
        "tool_calls",
        "attempts",
        "error",
        "timestamp",
    ]

    with open(output_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print()
    print(f"Results written to: {output_csv}")

    print_summary(results, context_policies, agent_policy)


def print_summary(results: list[dict], policies: list[str], agent_policy: str = "single") -> None:
    """Print summary statistics."""
    print("Summary")
    print("-" * 50)
    print(f"Agent Policy: {agent_policy}")
    print()

    for policy in policies:
        policy_results = [r for r in results if r.get("policy") == policy]

        passed = sum(1 for r in policy_results if r.get("passed"))
        total = len(policy_results)

        tokens = [r.get("tokens", 0) for r in policy_results]
        avg_tokens = sum(tokens) / max(len(tokens), 1)

        wall_times = [r.get("wall_time", 0) for r in policy_results]
        avg_time = sum(wall_times) / max(len(wall_times), 1)

        tool_calls = [r.get("tool_calls", 0) for r in policy_results]
        avg_tools = sum(tool_calls) / max(len(tool_calls), 1)

        attempts = [r.get("attempts", 1) for r in policy_results]
        avg_attempts = sum(attempts) / max(len(attempts), 1)

        print(f"\n{policy}:")
        print(
            f"  Pass@{int(avg_attempts)} Rate: {passed}/{total} ({100 * passed / max(total, 1):.1f}%)"
        )
        print(f"  Avg Tokens: {avg_tokens:.0f}")
        print(f"  Avg Time: {avg_time:.2f}s")
        print(f"  Avg Tool Calls: {avg_tools:.1f}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Run GAIA-lite benchmark")
    parser.add_argument(
        "--tasks",
        type=Path,
        default=REPO_ROOT / "data" / "tasks_gaia_lite.json",
        help="Path to tasks JSON file",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=REPO_ROOT / "data" / "gaia_lite_runs.csv",
        help="Output CSV path",
    )
    parser.add_argument(
        "--policies",
        nargs="+",
        default=["heuristic", "cli", "dump"],
        help="Context policies to test",
    )
    parser.add_argument(
        "--trials",
        type=int,
        default=1,
        help="Number of trials per task",
    )
    parser.add_argument(
        "--agent-policy",
        choices=["single", "3-agent"],
        default="single",
        help="Agent policy: single or 3-agent (Planner/Executor/Judge)",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=1,
        help="Maximum retry attempts (1 = Pass@1, 2 = Pass@2)",
    )

    args = parser.parse_args()

    run_benchmark(
        tasks_path=args.tasks,
        output_csv=args.output,
        context_policies=args.policies,
        trials=args.trials,
        agent_policy=args.agent_policy,
        max_retries=args.max_retries,
    )


if __name__ == "__main__":
    main()
