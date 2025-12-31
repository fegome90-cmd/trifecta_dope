#### A) cli_commands.nl_triggers
```diff
  cli_commands:
    priority: 3
    nl_triggers:
      - "ctx search"
      - "ctx get"
      - "ctx sync"
      - "ctx stats"
      - "list commands"
+     - "typer commands"     # NEW
+     - "available commands" # NEW
```
