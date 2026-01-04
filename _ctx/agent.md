---
segment: .
scope: Verification
repo_root: /Users/felipe_gonzalez/Developer/agent_h
last_verified: 2025-12-29
default_profile: impl_patch
---

# Agent Context - .

## Source of Truth
| Sección | Fuente |
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
- <!-- Listar dependencias principales de producción -->

**Development:**
- <!-- Listar dependencias de desarrollo -->

## Configuration

**Archivos de configuración:**
```
./
├── .env                    # Variables de entorno (local)
├── .env.example            # Template de variables
├── pyproject.toml          # Config Python (si aplica)
└── package.json            # Config Node (si aplica)
```

**Variables de entorno clave:**
```bash
# Agregar variables específicas del segmento
# Ejemplo:
DATABASE_URL=              # URL de base de datos
API_KEY=                   # Clave de API externa
LOG_LEVEL=info             # Nivel de logging
```

## Gates (Comandos de Verificación)

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
- <!-- ¿Qué módulos/deps necesitas primero? -->

**Downstream Consumers:**
- <!-- ¿Quién usa este segmento? -->

**API Contracts:**
- <!-- Endpoints, funciones, o interfaces expuestas -->

## Architecture Notes

<!-- Patrones de diseño, decisiones arquitectónicas, trade-offs -->

**Design Patterns:**
- <!-- Ej: Repository Pattern, Factory, Observer -->

**Key Decisions:**
- <!-- Por qué se eligió cierta tecnología o enfoque -->

**Known Limitations:**
- <!-- Limitaciones conocidas del segmento -->
