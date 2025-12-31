#### 3. El Guardián (The Builder Protocol)

Aquí es donde matamos el riesgo de Supply Chain. Cuando ejecutas `ctx build`:

1. **Lectura:** El builder lee el archivo local `python.md`.
2. **Hashing:** Calcula el SHA-256 del contenido actual en memoria.
3. **Verificación (The Gate):**
* Compara el Hash Calculado vs. Hash en `trifecta.lock`.
* **¿Coinciden?** ✅ Procede. Inyecta el contenido.
* **¿No Coinciden?** ❌ **STOP CRÍTICO**.
* *Alerta:* "Security Mismatch! El archivo `python.md` ha cambiado desde la última vez. El contenido no es confiable."
* *Acción:* El build falla. No se genera nada.
