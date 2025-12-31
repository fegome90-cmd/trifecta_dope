## 2. Setup del entorno

```bash
cd /Users/felipe_gonzalez/Developer/agent_h/trifecta_dope
uv sync
source .venv/bin/activate
python ~/Developer/Minirag/scripts/install_improved.py --source ~/Developer/Minirag
```

Notas:
- Si falta pip en el venv: `python -m ensurepip --upgrade`.
- Si el script falla, revisa `~/Developer/Minirag/INSTALLATION_GUIDE.md`.
