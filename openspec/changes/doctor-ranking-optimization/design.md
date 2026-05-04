# Design: doctor-ranking-optimization

Add `resolve_doctor_alias_match()` to `scripts/skill-hub`. It normalizes whitespace/case and matches only the three verified weak phrases. If the regular canonical alias resolver does not find a match, this resolver supplies `skill-hub-doctor`, and the existing alias rendering block prints canonical result + additional BM25 results.

This avoids BM25 changes, generated segment edits, or search_hints keyword stuffing.
