import json
import statistics
from collections import defaultdict

from pathlib import Path

EVENTS_FILE = Path("_ctx/telemetry/events.jsonl")


def analyze_telemetry():
    if not EVENTS_FILE.exists():
        print(f"File not found: {EVENTS_FILE}")
        return

    events = []
    with open(EVENTS_FILE, "r") as f:
        for line in f:
            if line.strip():
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    if not events:
        print("No events found.")
        return

    # --- CATEGORIZATION STRATEGY ---
    # We define "Eras" based on command functionality
    categories = {
        "1. Core (Sync/Build)": ["ctx.sync", "ctx.build", "ctx.validate", "ctx.sync.stub_regen"],
        "2. Progressive Disclosure": ["ctx.search", "ctx.get"],
        "3. AST / M1 (Symbols)": ["ast.symbols", "ast.hover", "ast.snippet"],
        "4. System / CLI": ["init", "cli.create"],
    }

    stats = defaultdict(
        lambda: {
            "count": 0,
            "errors": 0,
            "error_types": defaultdict(int),
            "latencies": [],
            "first_seen": None,
            "last_seen": None,
        }
    )

    # Sort by time to be sure
    # Handle formats: "2026-01-03T23:09:55-0300" (ISO 8601 strict) or older formats if any
    # Simple sort by string is usually mostly okay for ISO, but let's just iterate

    for e in events:
        cmd = e.get("cmd", "unknown")
        result = e.get("result", {})
        status = result.get("status", "ok")
        timing = e.get("timing_ms", 0)
        ts_str = e.get("ts", "")

        # Determine Category
        matched_cat = "5. Other"
        for cat_name, keywords in categories.items():
            if cmd in keywords:
                matched_cat = cat_name
                break
            # Fallback for partial matches like "ctx.get"
            for k in keywords:
                if k in cmd:  # Substring match
                    matched_cat = cat_name
                    break
            if matched_cat != "5. Other":
                break

        s = stats[matched_cat]
        s["count"] += 1
        s["latencies"].append(timing)

        if s["first_seen"] is None:
            s["first_seen"] = ts_str
        s["last_seen"] = ts_str

        if status != "ok" or (isinstance(result, dict) and result.get("error_code")):
            s["errors"] += 1
            err_code = result.get("error_code", "UNKNOWN_ERROR")
            if not err_code:
                err_code = "GENERIC_FAILURE"
            s["error_types"][err_code] += 1

    # --- GENERATE REPORT ---
    print("# 📊 Análisis Estadístico de Telemetría Trifecta")
    print(f"\n**Total Eventos**: {len(events)}")
    print(f"**Rango de Análisis**: {events[0].get('ts')} -> {events[-1].get('ts')}\n")

    print(
        "| Fase / Avance | Total Cmds | Success Rate | Latencia P50 (ms) | P95 (ms) | Errores Top |"
    )
    print("| :--- | :---: | :---: | :---: | :---: | :--- |")

    sorted_cats = sorted(stats.keys())

    for cat in sorted_cats:
        data = stats[cat]
        count = data["count"]
        if count == 0:
            continue

        errors = data["errors"]
        success_rate = ((count - errors) / count) * 100

        lats = sorted(data["latencies"])
        p50 = statistics.median(lats) if lats else 0
        p95 = lats[int(len(lats) * 0.95)] if lats else 0

        # Top 2 errors
        top_errs = sorted(data["error_types"].items(), key=lambda x: x[1], reverse=True)[:2]
        err_str = ", ".join([f"{k}({v})" for k, v in top_errs]) if top_errs else "None"
        if not err_str:
            err_str = "None"

        print(
            f"| **{cat}** | {count} | {success_rate:.1f}% | {p50:.1f}ms | {p95:.1f}ms | {err_str} |"
        )

    print("\n## 🔎 Insights por Fase")

    for cat in sorted_cats:
        data = stats[cat]
        if data["count"] == 0:
            continue
        print(f"\n### {cat}")
        print(f"- **Actividad Inicia**: {data['first_seen']}")
        print(f"- **Última Actividad**: {data['last_seen']}")
        if data["error_types"]:
            print("- **Distribución de Errores**:")
            for k, v in sorted(data["error_types"].items(), key=lambda x: x[1], reverse=True):
                print(f"  - `{k}`: {v}")


if __name__ == "__main__":
    analyze_telemetry()
