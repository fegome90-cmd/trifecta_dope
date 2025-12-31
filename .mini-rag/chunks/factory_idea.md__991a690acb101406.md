#### 1. El `AGENTS.md`: La Constitución del Proyecto

En lugar de un prompt gigante en el chat, cada repositorio de proyecto tendrá este archivo en la raíz.

**Ubicación:** `/projects/<segment>/AGENTS.md`
**Propósito:** Definir las "Leyes de la Física" de ese proyecto específico.

```markdown
# Normas de Ingeniería para el Proyecto MedLogger

## 1. Arquitectura
- Usamos Clean Architecture estricta.
- NUNCA importes Infraestructura dentro de Dominio.
- Si creas un Caso de Uso, DEBES crear su Test Unitario correspondiente inmediatamente.

## 2. Estilo y Linting
- Python: Seguimos PEP8 estricto + Black formatter.
- No toleramos funciones de más de 20 líneas.

## 3. Seguridad
- Prohibido hardcodear credenciales. Usa `os.getenv`.
- No leas archivos >1MB sin usar streams.

```

**Integración en Trifecta:**
Cuando el agente arranca (`trifecta ctx build`), lo **primero** que se inyecta en su System Context es el contenido de `AGENTS.md`. Es su lectura obligatoria antes de trabajar.
