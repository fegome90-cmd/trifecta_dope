## Error Prompt Format

When a command fails (`returncode != 0`), the harness generates an Error Prompt Card:

```
❌ Command Failed: <command>

Exit Code: <int>
Error Class: <class>
Error Code: <code>

Cause:
<detailed cause from Error Card>

Recovery Steps:
1. <deterministic step 1>
2. <deterministic step 2>
3. <deterministic step 3>
```
