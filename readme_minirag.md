# Mini-RAG (Guia Rapida)

Mini-RAG es una herramienta de desarrollo para consultar docs del CLI. No es parte del runtime de Trifecta.

## Setup (una vez)

```bash
cd /Users/felipe_gonzalez/Developer/agent_h/trifecta_dope
uv sync

# Instalar Mini-RAG desde el repo local
source .venv/bin/activate
python ~/Developer/Minirag/scripts/install_improved.py --source ~/Developer/Minirag
```

## Indexar

```bash
make minirag-index
```

## Consultar

```bash
make minirag-query MINIRAG_QUERY="ctx search"
```

## Bench rapido

```bash
bash minirag-eval/run_bench.sh negative_rejection
python minirag-eval/summarize_results.py
```

## Troubleshooting

- Mini-RAG no existe: re-instala con el script `scripts/install_improved.py`.
- Falla con pip: `python -m ensurepip --upgrade` y reintenta.
- Cambiaste docs: re-ejecuta `make minirag-index`.

Para detalles completos: `docs/minirag/manual_uso.md`.
