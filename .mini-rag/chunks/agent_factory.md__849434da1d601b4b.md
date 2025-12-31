# Uso: python compiler.py AGENTS.md > sgconfig.yml
    input_file = "AGENTS.md"
    result = parse_agents_md(input_file)
    print(yaml.dump(result, sort_keys=False))

```

### 2. El Resultado Compilado (`sgconfig.yml`)

Si ejecutas el script anterior sobre tu `AGENTS.md`, obtienes esto automáticamente. Esto es lo que `ast-grep` consume:

```yaml
rules:
  - id: core-isolation
    message: La capa 'core' no puede importar desde 'api' o 'ui'.
    severity: error
    language: TypeScript
    rule:
      pattern: import $IMPORTS from "$SOURCE"
      all:
        - inside:
            subdir: src/core/
        - has:
            field: source
            regex: src/api/|src/ui/

  - id: no-eval
    message: El uso de 'eval' está prohibido.
    severity: error
    language: TypeScript
    rule:
      pattern: eval($$$ARGS)
