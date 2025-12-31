### Máquina de Estados

```
┌─────────────┐  ``` o ~~~  ┌──────────────┐
│  in_fence   │ ──────────→ │  in_fence    │
│   = False   │             │   = True     │
└─────────────┘             └──────────────┘
      ↑                           │
      │       ``` o ~~~            │
      └───────────────────────────┘
```

**Regla**: Si `in_fence == True`, ignorar headings.

---
