# Decisión
    if linter_result.passed:
        new_state = state.update(current_code=agent_output.code) # Inmutable
        return Ok(new_state)
    else:
        feedback = create_feedback(linter_result) # Pura
        new_state = state.add_to_history(feedback) # Inmutable
        return run_generative_loop(new_state, max_retries - 1) # Recursión


5. run_user_test(state: AgentState) -> Result[FinalCode, Error]

•
Ejecuta el test del usuario contra el código validado.

•
Si pasa, devuelve Ok(FinalCode).

•
Si falla, devuelve Err(TestFailed).

Fase 3: Composición con Mónadas (Result)

El uso de Result (o Either en otros lenguajes) es no negociable. Elimina la necesidad de try/except y hace que el flujo de errores sea explícito y seguro.

Python
