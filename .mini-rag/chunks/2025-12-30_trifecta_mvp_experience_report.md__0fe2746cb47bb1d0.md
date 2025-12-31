### Flujo Típico (Plan A)
```
1. ctx sync --segment .          [2s build + validate]
2. ctx search --segment .        [queries hasta hit relevante]
3. ctx get --segment . --ids X   [retrieval bajo presupuesto]
4. [Acción basada en contexto]
5. session append                [log en session.md]
```
