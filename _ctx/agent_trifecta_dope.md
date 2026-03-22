---
segment: trifecta_dope
scope: Scope
repo_root: /Users/felipe_gonzalez/Developer/agent_h/trifecta_dope
last_verified: 2026-03-06
default_profile: impl_patch
---

# Agent Context - Trifecta_Dope

## Source of Truth
| Seccion | Fuente |
|---------|--------|
| LLM Roles | [skill.md](../skill.md) |
| Providers | `hemdov/src/hemdov/infrastructure/config/providers.yaml` |

## Tech Stack
<!-- Lenguajes, frameworks, y herramientas principales -->

**Lenguajes:**
- <!-- Ej: Python 3.11+, TypeScript 5.x -->

**Frameworks:**
- <!-- Ej: FastAPI, React, Pydantic -->

**Herramientas:**
- <!-- Ej: pytest, ruff, uv, npm -->

## Dependencies

**Runtime:**
- <!-- Listar dependencias principales de produccion -->

**Development:**
- <!-- Listar dependencias de desarrollo -->

## Configuration

**Archivos de configuracion:**
```
trifecta_dope/
|-- .env                    # Variables de entorno (local)
|-- .env.example            # Template de variables
|-- pyproject.toml          # Config Python (si aplica)
|__ package.json            # Config Node (si aplica)
```

**Variables de entorno clave:**
```bash
# Agregar variables especificas del segmento
# Ejemplo:
DATABASE_URL=              # URL de base de datos
API_KEY=                   # Clave de API externa
LOG_LEVEL=info             # Nivel de logging
```

## Gates (Comandos de Verificacion)

**Unit Tests:**
```bash
# Python
pytest tests/unit/ -v

# Node/TypeScript
npm test
# o
jest tests/unit/
```

**Integration Tests:**
```bash
# Python
pytest tests/integration/ -v

# Node
npm run test:integration
```

**Linting:**
```bash
# Python
ruff check .
black --check .

# Node
npm run lint
```

**Type Checking:**
```bash
# Python (mypy)
mypy src/

# TypeScript
npm run type-check
```

**Build:**
```bash
# Python
pip install -e .

# Node
npm run build
```

## Integration Points

**Upstream Dependencies:**
- <!-- Que modulos/deps necesitas primero? -->

**Downstream Consumers:**
- <!-- Quien usa este segmento? -->

**API Contracts:**
- <!-- Endpoints, funciones, o interfaces expuestas -->

## Architecture Notes

<!-- Patrones de disenio, decisiones arquitectonicas, trade-offs -->

**Design Patterns:**
- <!-- Ej: Repository Pattern, Factory, Observer -->

**Key Decisions:**
- <!-- Por que se eligio cierta tecnologia o enfoque -->

**Known Limitations:**
- <!-- Limitaciones conocidas del segmento -->

