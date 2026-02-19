#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, getcontext
from pathlib import Path
from typing import Any, cast

from tiktoken import Encoding  # type: ignore[import-not-found]
import tiktoken

getcontext().prec = 28

ROOT = Path(__file__).resolve().parents[1]
EVENTS = ROOT / "_ctx/telemetry/events.jsonl"
AUDIT_DIR = ROOT / "_ctx/audits/token_audit"
SYNTHESIS_OUT_FILE = AUDIT_DIR / "synthesis_final.txt"
SYNTHESIS_PROMPT_FILE = AUDIT_DIR / "synthesis_prompt.txt"
REPORT_FILE = AUDIT_DIR / "REPORT.md"
RESULTS_FILE = AUDIT_DIR / "results.json"

RUN_SEARCH = "run_1771428828"
RUN_GET = "run_1771428838"

INPUT_PER_1M = Decimal("1.75")
OUTPUT_PER_1M = Decimal("14.00")
CACHED_INPUT_PER_1M = Decimal("0.175")

B1_FILES = ["docs/backlog/WORKFLOW.md"]
B2_FILES = [
    "docs/backlog/WORKFLOW.md",
    "docs/CLI_WORKFLOW.md",
    "docs/guides/work_orders_usage.md",
    "docs/plans/2026-01-05-backlog-wo-dod-pipeline-plan.md",
]
B3_FILES = [
    "docs/backlog/WORKFLOW.md",
    "docs/CLI_WORKFLOW.md",
    "docs/guides/work_orders_usage.md",
    "docs/plans/2026-01-05-backlog-wo-dod-pipeline-plan.md",
    "scripts/ctx_wo_finish.py",
    "scripts/verify.sh",
    "_ctx/jobs/pending/WO-0056.yaml",
]


@dataclass
class Costs:
    cost_in: Decimal
    cost_out: Decimal

    @property
    def total(self) -> Decimal:
        return self.cost_in + self.cost_out


def _enc() -> Encoding:
    return tiktoken.encoding_for_model("gpt-4.1")


def tok_text(text: str) -> int:
    return len(_enc().encode(text))


def tok_json(obj: Any) -> int:
    payload = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return tok_text(payload)


def write_synthesis_telemetry(
    tokens_in: int | None,
    tokens_out: int,
    in_type: str,
    timing_ms: int = 0,
) -> None:
    """Append llm.synthesis telemetry event following PR#1 schema."""
    event = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "run_id": f"audit_{int(time.time())}",
        "segment_id": "token_audit",
        "cmd": "llm.synthesis",
        "args": {"model_price_profile": "gpt-5.2"},
        "result": {"tokens_in": tokens_in, "tokens_out": tokens_out},
        "timing_ms": max(1, timing_ms),
        "warnings": [],
        "x": {"in_type": in_type},
    }
    with EVENTS.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def load_event(run_id: str, cmd: str) -> dict[str, Any]:
    for line in EVENTS.read_text(encoding="utf-8").splitlines():
        row = cast(dict[str, Any], json.loads(line))
        if row.get("run_id") == run_id and row.get("cmd") == cmd:
            return row
    raise RuntimeError(f"Missing event run_id={run_id} cmd={cmd}")


def parse_ts(ts: str) -> datetime:
    # handles both "...-0300" and ISO with colon timezone
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"
    if len(ts) >= 5 and (ts[-5] in {"+", "-"}) and ts[-3] != ":":
        ts = ts[:-2] + ":" + ts[-2:]
    return datetime.fromisoformat(ts)


def dedupe(items: list[str]) -> list[str]:
    out: list[str] = []
    for item in items:
        if item not in out:
            out.append(item)
    return out


def sum_files_tokens(files: list[str]) -> tuple[int, list[dict[str, Any]]]:
    total = 0
    rows: list[dict[str, Any]] = []
    for rel in dedupe(files):
        path = ROOT / rel
        tokens = tok_text(path.read_text(encoding="utf-8"))
        total += tokens
        rows.append({"file": str(path), "tokens_in": tokens, "type": "MEDIDO"})
    return total, rows


def costs(tokens_in: int, tokens_out: int) -> Costs:
    return Costs(
        cost_in=Decimal(tokens_in) * INPUT_PER_1M / Decimal(1_000_000),
        cost_out=Decimal(tokens_out) * OUTPUT_PER_1M / Decimal(1_000_000),
    )


def fmt(v: Decimal) -> str:
    return format(v, "f")


def savings_pct(base: int, current: int) -> str:
    if base == 0:
        return "0"
    return str((Decimal(base - current) / Decimal(base)) * Decimal(100))


def detect_synth_in_status(search_ev: dict[str, Any], get_ev: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {
        "status": "MISSING",
        "tokens": None,
        "type": "MISSING",
        "reason": "Prompt final no está ligado de forma trazable a la interacción original (run_1771428828 + run_1771428838)",
        "candidate_file": str(SYNTHESIS_PROMPT_FILE),
        "candidate_tokens": None,
        "candidate_type": None,
    }

    try:
        prompt_text = SYNTHESIS_PROMPT_FILE.read_text(encoding="utf-8")
    except FileNotFoundError:
        result["reason"] = "No existe synthesis_prompt.txt"
        return result

    candidate_tokens = tok_text(prompt_text)
    result["candidate_tokens"] = candidate_tokens
    result["candidate_type"] = "ESTIMADO"

    # Forensic guard: prompt must be at most as new as synthesis output and tied to the interaction time.
    prompt_mtime = SYNTHESIS_PROMPT_FILE.stat().st_mtime
    out_mtime = SYNTHESIS_OUT_FILE.stat().st_mtime if SYNTHESIS_OUT_FILE.exists() else 0.0
    interaction_end = max(parse_ts(search_ev["ts"]), parse_ts(get_ev["ts"]))
    interaction_end_ts = interaction_end.timestamp()

    if prompt_mtime > out_mtime or prompt_mtime > interaction_end_ts:
        result["reason"] = (
            "synthesis_prompt.txt existe pero fue generado post-hoc (mtime posterior a la interacción/salida), "
            "no se usa como MEDIDO para este experimento"
        )
        return result

    # Even if timing fits, there is no hard linkage field in telemetry for this interaction.
    # Still, we use the candidate tokens as ESTIMADO (not MEDIDO) for the audit.
    result["status"] = "ESTIMATED"
    result["tokens"] = candidate_tokens
    result["type"] = "ESTIMADO"
    result["reason"] = "synthesis_prompt.txt no tiene linkage explícito (run_id/interaction_id) con la interacción auditada, usado como ESTIMADO"
    return result


def build_report(data: dict[str, Any]) -> str:
    a = data["section_a_tools_only"]
    b = data["baselines"]
    s = data["savings_tools_only"]
    t = data["task_complete"]

    lines: list[str] = []
    lines.append("A) Definición del experimento")
    lines.append("- Experimento: 'required artifacts en cierre de WO'.")
    lines.append("- Interacción definida: tools + síntesis final.")
    lines.append("- Precio congelado GPT-5.2: INPUT=1.75, OUTPUT=14.00, CACHED_INPUT=0.175 (cached no aplicado).")
    lines.append("- Método de tokens: tiktoken `encoding_for_model(\"gpt-4.1\")`, UTF-8, JSON canónico para args/result.")
    lines.append("")

    lines.append("B) Datos medidos")
    lines.append("| Item | Tokens In | Tokens Out | Fuente | Tipo |")
    lines.append("|---|---:|---:|---|---|")
    lines.append(f"| ctx.search ({a['runs']['search_run_id']}) | {a['tools']['search']['tokens_in']} | {a['tools']['search']['tokens_out']} | {EVENTS} | MEDIDO |")
    lines.append(f"| ctx.get ({a['runs']['get_run_id']}) | {a['tools']['get']['tokens_in']} | {a['tools']['get']['tokens_out']} | {EVENTS} | MEDIDO |")
    lines.append(f"| A tools totals | {a['tools']['totals']['tokens_in']} | {a['tools']['totals']['tokens_out']} | {EVENTS} | MEDIDO |")
    lines.append(f"| Synthesis OUT | 0 | {data['synthesis']['out_tokens']} | {SYNTHESIS_OUT_FILE} | MEDIDO |")
    lines.append(
        f"| Synthesis IN | {data['synthesis']['in_tokens'] if data['synthesis']['in_tokens'] is not None else 'MISSING'} | 0 | {data['synthesis']['in_source']} | {data['synthesis']['in_type']} |"
    )
    lines.append("")

    lines.append("C) Escenario A tools-only (100% medido)")
    lines.append(f"- TOTAL_IN_A_TOOLS = {a['tools']['totals']['tokens_in']}")
    lines.append(f"- TOTAL_OUT_A_TOOLS = {a['tools']['totals']['tokens_out']}")
    lines.append(f"- TOTAL_A_TOOLS_ONLY = {a['tools']['totals']['tokens_total']}")
    lines.append(f"- COST_IN_A_TOOLS = {a['tools']['cost']['cost_in']}")
    lines.append(f"- COST_OUT_A_TOOLS = {a['tools']['cost']['cost_out']}")
    lines.append(f"- COST_TOTAL_A_TOOLS = {a['tools']['cost']['cost_total']}")
    lines.append("")

    lines.append("D) Baselines B1/B2/B3 (input dumping medido)")
    for key in ("B1", "B2", "B3"):
        row = b[key]
        lines.append(f"- {key}: TOKENS_IN={row['tokens_in']} COST_IN={row['cost_in']} (MEDIDO, dedupe)")
    lines.append("")

    lines.append("E) Resultados tools-only")
    lines.append("- Fórmula % ahorro input: (TOKENS_IN_B - TOKENS_IN_A_TOOLS) / TOKENS_IN_B * 100")
    for key in ("vs_B1", "vs_B2", "vs_B3"):
        row = s[key]
        lines.append(
            f"- {key}: Δtokens_in={row['delta_tokens_in']} Δcost_in={row['delta_cost_in']} ahorro_pct_in={row['savings_pct_in']}"
        )
    lines.append("")

    lines.append("F) Task-complete")
    lines.append(f"- status: {t['status']}")
    lines.append(f"- missing: {', '.join(t['missing'])}")
    lines.append("- cannot compute exact %/cost task-complete con datos actuales.")
    lines.append("")

    lines.append("G) Limitaciones")
    lines.append("- tools-only y synthesis final OUT están medidos; synthesis IN de la interacción original no está medido de forma trazable.")
    lines.append("- B1/B2/B3 no tienen síntesis manual persistida (prompt+out) por escenario.")
    lines.append("")

    lines.append("H) Próxima instrumentación mínima")
    lines.append("- En cada respuesta final, persistir `interaction_id`, `synthesis_prompt_tokens`, `synthesis_out_tokens` en telemetry.")
    lines.append("- Crear artefactos por baseline: `b*_synthesis_prompt.txt` y `b*_synthesis_out.txt`.")
    lines.append("- Repro command: `python3 scripts/audit_tokens.py`.")

    return "\n".join(lines) + "\n"


def main() -> None:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)

    ev_search = load_event(RUN_SEARCH, "ctx.search")
    ev_get = load_event(RUN_GET, "ctx.get")

    search_in = tok_json(ev_search["args"])
    search_out = tok_json(ev_search["result"])
    get_in = tok_json(ev_get["args"])
    get_out = int(ev_get["result"]["total_tokens"])

    total_in_a_tools = search_in + get_in
    total_out_a_tools = search_out + get_out
    total_a_tools = total_in_a_tools + total_out_a_tools

    c_a_tools = costs(total_in_a_tools, total_out_a_tools)

    if not SYNTHESIS_OUT_FILE.exists():
        sys.exit("MISSING: synthesis_final.txt required for task-complete audit")
    synth_out = tok_text(SYNTHESIS_OUT_FILE.read_text(encoding="utf-8"))
    synth_in_state = detect_synth_in_status(ev_search, ev_get)

    # Write synthesis telemetry event (timing_ms=0 is intentional - telemetry is post-hoc)
    write_synthesis_telemetry(
        tokens_in=synth_in_state["tokens"],
        tokens_out=synth_out,
        in_type=synth_in_state["type"],
    )

    b1_in, b1_rows = sum_files_tokens(B1_FILES)
    b2_in, b2_rows = sum_files_tokens(B2_FILES)
    b3_in, b3_rows = sum_files_tokens(B3_FILES)

    c_b1_in = costs(b1_in, 0)
    c_b2_in = costs(b2_in, 0)
    c_b3_in = costs(b3_in, 0)

    task_missing = [
        "SYNTH_IN_TOKENS",
        "B1_SYNTH_PROMPT_TOKENS",
        "B1_SYNTH_OUT_TOKENS",
        "B2_SYNTH_PROMPT_TOKENS",
        "B2_SYNTH_OUT_TOKENS",
        "B3_SYNTH_PROMPT_TOKENS",
        "B3_SYNTH_OUT_TOKENS",
    ]

    data: dict[str, Any] = {
        "section_a_tools_only": {
            "runs": {
                "search_run_id": RUN_SEARCH,
                "get_run_id": RUN_GET,
            },
            "tools": {
                "search": {
                    "tokens_in": search_in,
                    "tokens_out": search_out,
                    "type": "MEDIDO",
                },
                "get": {
                    "tokens_in": get_in,
                    "tokens_out": get_out,
                    "type": "MEDIDO",
                    "tokens_out_source": "ctx.get.result.total_tokens",
                },
                "totals": {
                    "tokens_in": total_in_a_tools,
                    "tokens_out": total_out_a_tools,
                    "tokens_total": total_a_tools,
                    "type": "MEDIDO",
                },
                "cost": {
                    "cost_in": fmt(c_a_tools.cost_in),
                    "cost_out": fmt(c_a_tools.cost_out),
                    "cost_total": fmt(c_a_tools.total),
                },
            },
        },
        "synthesis": {
            "out_tokens": synth_out,
            "out_type": "MEDIDO",
            "out_source": str(SYNTHESIS_OUT_FILE),
            "in_tokens": synth_in_state["tokens"],
            "in_type": synth_in_state["type"],
            "in_source": synth_in_state["candidate_file"],
            "in_reason": synth_in_state["reason"],
            "candidate_tokens": synth_in_state["candidate_tokens"],
            "candidate_type": synth_in_state["candidate_type"],
        },
        "baselines": {
            "B1": {
                "tokens_in": b1_in,
                "cost_in": fmt(c_b1_in.cost_in),
                "files": b1_rows,
                "type": "MEDIDO",
            },
            "B2": {
                "tokens_in": b2_in,
                "cost_in": fmt(c_b2_in.cost_in),
                "files": b2_rows,
                "type": "MEDIDO",
            },
            "B3": {
                "tokens_in": b3_in,
                "cost_in": fmt(c_b3_in.cost_in),
                "files": b3_rows,
                "type": "MEDIDO",
            },
        },
        "savings_tools_only": {
            "vs_B1": {
                "delta_tokens_in": b1_in - total_in_a_tools,
                "delta_cost_in": fmt(c_b1_in.cost_in - c_a_tools.cost_in),
                "savings_pct_in": savings_pct(b1_in, total_in_a_tools),
            },
            "vs_B2": {
                "delta_tokens_in": b2_in - total_in_a_tools,
                "delta_cost_in": fmt(c_b2_in.cost_in - c_a_tools.cost_in),
                "savings_pct_in": savings_pct(b2_in, total_in_a_tools),
            },
            "vs_B3": {
                "delta_tokens_in": b3_in - total_in_a_tools,
                "delta_cost_in": fmt(c_b3_in.cost_in - c_a_tools.cost_in),
                "savings_pct_in": savings_pct(b3_in, total_in_a_tools),
            },
        },
        "task_complete": {
            "status": "blocked",
            "missing": task_missing,
            "blocked_reason": "No existe medición trazable de SYNTH_IN para la interacción original y faltan síntesis manuales en B1/B2/B3",
        },
        "pricing": {
            "model": "GPT-5.2",
            "input_per_1m": str(INPUT_PER_1M),
            "output_per_1m": str(OUTPUT_PER_1M),
            "cached_input_per_1m": str(CACHED_INPUT_PER_1M),
            "cached_applied": False,
        },
        "repro": {
            "command": "python3 scripts/audit_tokens.py",
        },
    }

    RESULTS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    REPORT_FILE.write_text(build_report(data), encoding="utf-8")


if __name__ == "__main__":
    main()
