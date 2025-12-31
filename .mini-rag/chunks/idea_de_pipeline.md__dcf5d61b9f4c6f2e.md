### 2.2 Railway Oriented Programming (ROP)

El flujo de ejecución abandona el manejo de excepciones (`try/catch`) en favor de la Mónada `Result` (o `Either`).

* **Vía del Éxito (Success Track):** El agente genera código, pasa validaciones, pasa tests. El estado fluye transformándose.
* **Vía del Fallo (Failure Track):** Si ocurre un error (Linter, Test, Timeout), el flujo cambia de vía. El error no rompe el programa; se encapsula como un objeto de datos (`FailureContext`) que contiene el estado en el momento del fallo y la razón semántica.
* **Beneficio:** Permite que el sistema reaccione lógicamente a los errores (ej. "Intentar auto-corrección") en lugar de crashear.
