# digest ultra simple (mejorable): primeros 800 chars de cada doc
    digest = []
    for d in docs:
        doc_chunks = [c for c in all_chunks if c["doc"] == d["doc"]]
        head = "\n\n".join(c["text"] for c in doc_chunks[:2])[:800]
        digest.append({"doc": d["doc"], "digest": head})

    pack = {"docs": docs, "digest": digest, "index": index, "chunks": all_chunks}
    Path(out_path).write_text(json.dumps(pack, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 4:
        print("Usage: python3 build_pack.py a.md b.md c.md")
        raise SystemExit(2)
    out = build_pack(sys.argv[1:4])
    print(f"[ok] wrote {out}")


⸻

5) Cómo lo “cargas” al agente (sin derrochar tokens)

Prompt base (lo que SIEMPRE envías)

Incluye solo esto:
	•	Reglas de uso:
	•	“Tienes digest + index. Para detalles usa la tool get_context(id).”
	•	digest
	•	index (solo ID + título + preview)

Ejemplo de bloque para tu system prompt (conceptual, no enorme):

CONTEXT POLICY:
- You have DIGEST + INDEX.
- Never assume details not present in DIGEST/INDEX.
- If you need specifics, call get_context(chunk_id).
DIGEST:
...
INDEX:
- fp:0001 | Monads | ...preview...
...

Tool (lo que entrega texto completo cuando el agente lo pide)
