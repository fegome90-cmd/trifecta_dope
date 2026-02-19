from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import types
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "audit_tokens.py"


def load_module() -> Any:
    # Provide lightweight tiktoken stub for unit tests.
    fake_tiktoken = types.ModuleType("tiktoken")

    class _FakeEncoding:
        def encode(self, text: str) -> list[int]:
            return [ord(c) for c in text]

    def _encoding_for_model(_: str) -> _FakeEncoding:
        return _FakeEncoding()

    fake_tiktoken.encoding_for_model = _encoding_for_model  # type: ignore[attr-defined]
    fake_tiktoken.Encoding = _FakeEncoding  # type: ignore[attr-defined]
    sys.modules["tiktoken"] = fake_tiktoken

    spec = importlib.util.spec_from_file_location("audit_tokens_mod", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load audit_tokens.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["audit_tokens_mod"] = mod
    spec.loader.exec_module(mod)
    return mod


def setup_workspace(tmp_path: Path, with_prompt: bool) -> tuple[Any, Path]:
    root = tmp_path / "repo"
    (root / "_ctx/telemetry").mkdir(parents=True)
    (root / "_ctx/audits/token_audit").mkdir(parents=True)

    # Baseline files expected by script
    for rel in [
        "docs/backlog/WORKFLOW.md",
        "docs/CLI_WORKFLOW.md",
        "docs/guides/work_orders_usage.md",
        "docs/plans/2026-01-05-backlog-wo-dod-pipeline-plan.md",
        "scripts/ctx_wo_finish.py",
        "scripts/verify.sh",
        "_ctx/jobs/pending/WO-0056.yaml",
    ]:
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(f"content {rel}\n", encoding="utf-8")

    events = [
        {
            "ts": "2026-02-18T12:33:48-0300",
            "run_id": "run_1771428828",
            "segment_id": "6f25e381",
            "cmd": "ctx.search",
            "args": {
                "query_preview": "Find documentation about required artifacts in Work Order closure including tests.log lint.log handoff.md verification_report",
                "query_hash": "bb868761b690bdb6",
                "query_len": 125,
                "limit": 6,
                "alias_expanded": False,
                "alias_terms_count": 0,
                "alias_keys_used": [],
                "linter_query_class": "disabled",
                "linter_expanded": False,
                "linter_added_strong_count": 0,
                "linter_added_weak_count": 0,
                "linter_reasons": [],
            },
            "result": {
                "hits": 6,
                "returned_ids": [
                    "repo:docs/guides/work_orders_usage.md:179ef4e133",
                    "repo:docs/plans/2026-01-04-documentation-revision.md:93bfe4d123",
                    "repo:docs/backlog/WORKFLOW.md:724afc1c0b",
                    "ref:trifecta_dope/docs/CLI_WORKFLOW.md:900b828255",
                    "repo:docs/CLI_WORKFLOW.md:0dee3847a0",
                    "repo:docs/plans/2026-01-05-backlog-wo-dod-pipeline-plan.md:f96371f390",
                ],
            },
            "timing_ms": 1,
            "warnings": [],
            "x": {"source": "interactive", "build_sha": "6337d968", "mode": "search_only"},
        },
        {
            "ts": "2026-02-18T12:33:58-0300",
            "run_id": "run_1771428838",
            "segment_id": "6f25e381",
            "cmd": "ctx.get",
            "args": {
                "ids": ["repo:docs/backlog/WORKFLOW.md:724afc1c0b"],
                "mode": "excerpt",
                "budget": 2000,
                "max_chunks": None,
                "stop_on_evidence": False,
            },
            "result": {
                "chunks_returned": 1,
                "total_tokens": 255,
                "trimmed": False,
                "stop_reason": "complete",
                "chunks_requested": 1,
                "chars_returned_total": 1020,
                "evidence": {"strong_hit": False, "support": False},
            },
            "timing_ms": 1,
            "warnings": [],
            "x": {},
        },
    ]
    events_path = root / "_ctx/telemetry/events.jsonl"
    events_path.write_text("\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8")

    synth_out = root / "_ctx/audits/token_audit/synthesis_final.txt"
    synth_out.write_text("final synthesis output\n", encoding="utf-8")

    if with_prompt:
        synth_prompt = root / "_ctx/audits/token_audit/synthesis_prompt.txt"
        synth_prompt.write_text("final synthesis prompt\n", encoding="utf-8")

    mod = load_module()
    mod.ROOT = root
    mod.EVENTS = events_path
    mod.AUDIT_DIR = root / "_ctx/audits/token_audit"
    mod.SYNTHESIS_FILE = root / "_ctx/audits/token_audit/synthesis_final.txt"
    mod.SYNTHESIS_PROMPT_FILE = root / "_ctx/audits/token_audit/synthesis_prompt.txt"
    mod.SYNTHESIS_RESPONSE_FILE = root / "_ctx/audits/token_audit/synthesis_response.txt"
    mod.REPORT_FILE = root / "_ctx/audits/token_audit/REPORT.md"
    mod.RESULTS_FILE = root / "_ctx/audits/token_audit/results.json"

    return mod, root


def test_fails_when_synthesis_prompt_missing(tmp_path: Path) -> None:
    mod, root = setup_workspace(tmp_path, with_prompt=False)
    mod.main()  # Should NOT raise, uses graceful degradation

    results = json.loads((root / "_ctx/audits/token_audit/results.json").read_text(encoding="utf-8"))
    assert results["synthesis"]["in_type"] == "MISSING"
    assert results["synthesis"]["in_tokens"] is None


def test_records_llm_synthesis_and_computes_a_task_complete(tmp_path: Path) -> None:
    mod, root = setup_workspace(tmp_path, with_prompt=True)
    mod.main()

    results = json.loads((root / "_ctx/audits/token_audit/results.json").read_text(encoding="utf-8"))
    assert "in_tokens" in results["synthesis"]
    assert results["synthesis"]["out_tokens"] > 0
    assert results["synthesis"]["out_type"] == "MEDIDO"

    # Verify telemetry event written
    lines = (root / "_ctx/telemetry/events.jsonl").read_text(encoding="utf-8").strip().splitlines()
    llm = json.loads(lines[-1])
    assert llm["cmd"] == "llm.synthesis"
    assert llm["args"]["model_price_profile"] == "gpt-5.2"
    assert llm["result"]["tokens_in"] == results["synthesis"]["in_tokens"]
    assert llm["result"]["tokens_out"] == results["synthesis"]["out_tokens"]


def test_strict_mode_keeps_b_task_complete_missing_without_artifacts(tmp_path: Path) -> None:
    mod, root = setup_workspace(tmp_path, with_prompt=True)
    mod.main()

    results = json.loads((root / "_ctx/audits/token_audit/results.json").read_text(encoding="utf-8"))
    t = results["task_complete"]  # Direct access, not nested

    assert t["status"] == "blocked"
    assert "SYNTH_IN_TOKENS" in t["missing"]
    assert "B1_SYNTH_PROMPT_TOKENS" in t["missing"]
