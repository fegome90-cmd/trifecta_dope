schema v2** | Schema v1 es funcional; cambio es breaking change | Con migración plan | AP1: Schema debe estar versionado |
| **--src-root flag** | Agregar flags es scope creep; usar convención fija | Nunca (convención es suficiente) | AP5: Precedencia se complica |
| **Re-exports en ast_parser** | Tests deben importar desde módulos correctos; no false positives | Nunca (principio de import correcto) | AP9: Compat shims en capa equivocada |
| **stderr silencing** | Ocultar errores rompe auditabilidad | Nunca | AP6: Evidencia debe ser completa |
| **stdout parsing** | String parsing es frágil (AP1) | Nunca | AP1: Usar parsers tipados |
| ** cwd-based I/O** | CWD dependency rompe reproducibilidad | Nunca | AP3: Todo relativo a segment_root |
