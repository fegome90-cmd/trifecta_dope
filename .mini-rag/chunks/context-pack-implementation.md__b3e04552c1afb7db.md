### Qué hace:

1. **CRLF → LF**: Convierte terminaciones Windows a Unix
2. **Strip**: Elimina whitespace al inicio/final
3. **Collapse blank lines**: `\n\n\n+` → `\n\n`
4. **Trailing newline**: Asegura `\n` al final
