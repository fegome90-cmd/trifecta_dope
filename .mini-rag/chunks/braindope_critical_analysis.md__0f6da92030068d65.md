### 3. **Background Script es Frágil**

**PROPUESTA**: Script `.sh` corriendo en background.

**PROBLEMAS**:
- ¿Cómo detectas si el script murió?
- ¿Cómo lo reinicias automáticamente?
- ¿supervisor? ¿systemd? ¿launchd en macOS?
- ¿Qué pasa con entradas perdidas durante downtime?

**REALIDAD**: Background processes sin supervisión son una receta para bugs silenciosos.

**ALTERNATIVA MEJOR**: Hook directo en el CLI (síncrono), no background. Pero eso añade latencia.

---
