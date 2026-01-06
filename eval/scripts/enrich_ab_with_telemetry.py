import json
import sys
from pathlib import Path


def main():
    repo_root = Path(__file__).resolve().parents[3]
    ab_path = repo_root / "trifecta_dope" / "_ctx" / "metrics" / "field_exercises_v2_ab.json"
    events_path = repo_root / "trifecta_dope" / "_ctx" / "telemetry" / "events.jsonl"

    print(f"Loading AB results from {ab_path}")
    with open(ab_path) as f:
        ab_data = json.load(f)

    print(f"Loading events from {events_path}")
    events = []
    with open(events_path) as f:
        for line in f:
            if line.strip():
                try:
                    events.append(json.loads(line))
                except:
                    pass

    # Filter for ctx.search events
    search_events = [e for e in events if e.get("cmd") == "ctx.search"]
    print(f"Found {len(search_events)} search events")

    # We need to match AB queries to events.
    # We look for the most recent event for each query text that has linter enabled.
    # Note: simple query text match might be ambiguous if same query run multiple times.
    # But for this batch run, we assume the last instance is the correct one.

    matched = 0
    for item in ab_data:
        query_text = item["query"]
        # Find matching events (reverse order to find latest)
        candidates = [
            e
            for e in reversed(search_events)
            if e["args"].get("query_preview") == query_text
            # We want the ON run, so check if linter was potentially active
            # Usually linter_query_class != 'disabled' OR linter_expanded exists
            # Wait, OFF run might also log?
            # In OFF run: linter_query_class might be 'disabled' or missing?
            # Let's look at OFF log: "linter_query_class": "disabled"
            # In ON run: "linter_query_class": "vague" (or other)
            and e["args"].get("linter_query_class") != "disabled"
        ]

        if candidates:
            event = candidates[0]
            args = event["args"]

            # Enrich
            item["on"]["telemetry"]["linter_expanded"] = args.get("linter_expanded", False)
            item["on"]["telemetry"]["linter_query_class"] = args.get(
                "linter_query_class", "unknown"
            )
            item["on"]["telemetry"]["linter_reasons"] = args.get("linter_reasons", [])
            item["on"]["telemetry"]["query_hash"] = args.get("query_hash", "unknown")

            matched += 1
            # print(f"Matched {query_text[:20]}... -> Expanded: {args.get('linter_expanded')}")
        else:
            print(f"⚠️ No matching ON event found for: {query_text}")

    print(f"Enriched {matched}/{len(ab_data)} queries")

    with open(ab_path, "w") as f:
        json.dump(ab_data, f, indent=2)

    print("✅ Updated ab.json")


if __name__ == "__main__":
    main()
