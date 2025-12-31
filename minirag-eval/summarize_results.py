from __future__ import annotations

import json
from pathlib import Path


def parse_results(path: Path) -> dict[str, dict]:
    text = path.read_text(encoding="utf-8")
    sections = text.split("## Query: ")[1:]
    parsed: dict[str, dict] = {}
    for section in sections:
        lines = section.splitlines()
        query = lines[0].strip()
        json_start = section.find("{")
        json_end = section.find("\n---")
        json_blob = section[json_start : json_end if json_end != -1 else None].strip()
        parsed[query] = json.loads(json_blob)
    return parsed


def top_sources(payload: dict) -> list[str]:
    return [c.get("source", "") for c in payload.get("results", {}).get("chunks", [])[:5]]


def main() -> None:
    base = Path("minirag-eval/results")
    results = {
        "core": parse_results(Path("docs/testing/minirag_search_bench_results.md")),
        "negative_rejection": parse_results(base / "negative_rejection.md"),
        "ambiguous_multihop": parse_results(base / "ambiguous_multihop.md"),
        "temporal_recency": parse_results(base / "temporal_recency.md"),
        "contradictions": parse_results(base / "contradictions.md"),
        "noise_injection": parse_results(base / "noise_injection.md"),
        "lsp_ast_positive": parse_results(base / "lsp_ast_positive.md"),
    }

    query_sets = {
        "core": [
            "implementacion de ast",
            "ast parser referencia",
            "implementacion de lsp",
            "go to definition hover lsp",
            "context pack ingestion schema v1 digest index chunks",
            "trifecta ctx validate command",
            "progressive disclosure L0 L1 L2",
            "chunking fences headings",
            "skeletonizer tree-sitter ast parser",
            "lsp diagnostics hot files",
            "workspace symbols lsp search",
            "progressive disclosure hooks L0 L1 L2",
            "context pack json schema_version",
            "ctx search get excerpt budget",
            "ollama keep_alive retry_delay config",
            "index embeddings.npy metadata.json",
        ],
        "negative_rejection": [
            "politica de vacaciones del equipo",
            "receta de pasta carbonara",
            "resultados de las elecciones 2024 en francia",
            "guia de cultivo de tomates en casa",
            "manual de usuario de iphone 15",
        ],
        "ambiguous_multihop": [
            "roadmap_v2 y action_plan_v1.1 diferencias",
            "context-pack-ingestion vs context-pack-implementation diferencias",
            "trifecta-context-loading vs implementation_workflow",
            "telemetry_data_science_plan vs telemetry_analysis",
            "roadmap_v2 priorities vs research_roi_matrix",
        ],
        "temporal_recency": [
            "latest telemetry plan",
            "latest roadmap update",
            "most recent context pack plan",
            "latest implementation workflow",
            "latest context loading plan",
        ],
        "contradictions": [
            "trifecta usa embeddings",
            "trifecta es un rag",
            "mini-rag es parte de trifecta",
            "trifecta usa busqueda lexical",
            "trifecta indexa todo el repo",
        ],
        "noise_injection": [
            "trifecta ctx build receta pasta",
            "context pack ingestion futbol resultados",
            "telemetry analysis guitarra",
            "roadmap v2 meteorologia",
            "lsp diagnostics pizza",
        ],
        "lsp_ast_positive": [
            "implementacion de ast tree-sitter",
            "ast parser tree-sitter skeletonizer",
            "que extraer del AST",
            "implementacion de lsp symbols hover diagnostics",
            "workspace symbols lsp search",
            "lsp document symbols structure",
            "lsp go to definition hover",
            "lsp diagnostics hot files",
            "fase 3 ast lsp ide grade fluidity",
            "ast lsp hot files roadmap roi",
        ],
    }

    def core_pass(query: str) -> bool:
        payload = results["core"].get(query, {})
        chunks = payload.get("results", {}).get("chunks", [])[:5]
        if query == "implementacion de ast":
            return any(
                "integracion-ast-agentes.md" in (c.get("text", "") + c.get("source", ""))
                for c in chunks
            )
        if query == "ast parser referencia":
            return any("legacy/ast-parser.ts" in c.get("text", "") for c in chunks)
        if query == "implementacion de lsp":
            return any("trifecta-context-loading" in c.get("source", "") for c in chunks)
        if query == "go to definition hover lsp":
            return any("hover" in c.get("text", "").lower() for c in chunks)
        if query == "context pack ingestion schema v1 digest index chunks":
            return any("context-pack-ingestion" in c.get("source", "") for c in chunks)
        if query == "trifecta ctx validate command":
            return any("trifecta ctx validate" in c.get("text", "").lower() for c in chunks)
        if query == "progressive disclosure L0 L1 L2":
            return any(
                "l0" in c.get("text", "").lower() and "l1" in c.get("text", "").lower()
                for c in chunks
            )
        if query == "chunking fences headings":
            return any(
                "fence" in c.get("text", "").lower() or "heading" in c.get("text", "").lower()
                for c in chunks
            )
        if query == "skeletonizer tree-sitter ast parser":
            return any(
                "tree-sitter" in c.get("text", "").lower()
                or "skeletonizer" in c.get("text", "").lower()
                for c in chunks
            )
        if query == "lsp diagnostics hot files":
            return any(
                "diagnostics" in c.get("text", "").lower() and "lsp" in c.get("text", "").lower()
                for c in chunks
            )
        if query == "workspace symbols lsp search":
            return any("workspace_symbols" in c.get("text", "").lower() for c in chunks)
        if query == "progressive disclosure hooks L0 L1 L2":
            return any(
                "l0" in c.get("text", "").lower() and "l1" in c.get("text", "").lower()
                for c in chunks
            )
        if query == "context pack json schema_version":
            return any("schema_version" in c.get("text", "").lower() for c in chunks)
        if query == "ctx search get excerpt budget":
            txts = [c.get("text", "").lower() for c in chunks]
            return any("ctx search" in t and "ctx get" in t for t in txts)
        if query == "ollama keep_alive retry_delay config":
            return any(
                "keep_alive" in c.get("text", "").lower()
                or "retry_delay" in c.get("text", "").lower()
                for c in chunks
            )
        if query == "index embeddings.npy metadata.json":
            return any(
                "embeddings.npy" in c.get("text", "").lower()
                or "metadata.json" in c.get("text", "").lower()
                for c in chunks
            )
        return False

    def negative_pass(query: str) -> bool:
        payload = results["negative_rejection"].get(query, {})
        return payload.get("results", {}).get("chunks") == []

    def ambiguous_pass(query: str) -> bool:
        payload = results["ambiguous_multihop"].get(query, {})
        return any("all_bridges.md" in s for s in top_sources(payload))

    def temporal_pass(query: str) -> bool:
        payload = results["temporal_recency"].get(query, {})
        return any("all_bridges.md" in s for s in top_sources(payload))

    def contradictions_pass(query: str) -> bool:
        payload = results["contradictions"].get(query, {})
        return any("all_bridges.md" in s for s in top_sources(payload))

    def noise_pass(query: str) -> bool:
        payload = results["noise_injection"].get(query, {})
        return any("all_bridges.md" in s for s in top_sources(payload))

    def lsp_ast_pass(query: str) -> bool:
        payload = results["lsp_ast_positive"].get(query, {})
        sources = top_sources(payload)
        return any(
            "trifecta-context-loading" in s
            or "research_roi_matrix" in s
            or "agent_factory" in s
            or "all_bridges.md" in s
            for s in sources
        )

    matchers = {
        "core": core_pass,
        "negative_rejection": negative_pass,
        "ambiguous_multihop": ambiguous_pass,
        "temporal_recency": temporal_pass,
        "contradictions": contradictions_pass,
        "noise_injection": noise_pass,
        "lsp_ast_positive": lsp_ast_pass,
    }

    for module, qs in query_sets.items():
        matcher = matchers[module]
        passes = sum(1 for q in qs if matcher(q))
        print(f"{module}: {passes}/{len(qs)} PASS")


if __name__ == "__main__":
    main()
