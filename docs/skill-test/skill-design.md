# TestSprite Skill Design Blueprint

> Template for creating Claude Code skills that use TestSprite MCP

---

## Overview

This document provides blueprints for creating skills that integrate with the TestSprite MCP server. Based on the reverse-engineering session, these patterns ensure effective use of TestSprite's capabilities.

---

## Skill 1: testsprite-setup

### Purpose

Initialize TestSprite for a new project with proper configuration and code summary generation.

### Trigger

```
"set up testsprite"
"initialize automated testing"
"create test configuration"
```

### Skill Definition

```markdown
---
name: testsprite-setup
description: Initialize TestSprite MCP for a project
---

## Prerequisites

1. Verify project has testable endpoints (backend) or UI (frontend)
2. Check if `.testsprite/config.json` already exists
3. Ensure MCP server is accessible

## Workflow

### Step 1: Check Existing Config

```bash
ls -la .testsprite/config.json
```

- If exists: Skip to Step 3
- If missing: Continue to Step 2

### Step 2: Bootstrap

Call `mcp__TestSprite__testsprite_bootstrap` with:
- `localPort`: Detect from project (look for port in config/code)
- `type`: Detect from project (package.json → frontend, requirements.txt → backend)
- `projectPath`: Absolute path to project root
- `testScope`: "codebase" for full testing

### Step 3: Generate Code Summary

Call `mcp__TestSprite__testsprite_generate_code_summary`

**CRITICAL**: This tool returns instructions. The AI must:
1. Analyze project structure
2. Identify tech stack
3. Document features and endpoints
4. Write YAML to `testsprite_tests/tmp/code_summary.yaml`

### Code Summary Template

```yaml
version: "2"
type: backend  # or frontend
tech_stack:
  - [Language Version]
  - [Framework]
  - [Database]
features:
  - name: [Feature Name]
    description: [What it does]
    files:
      - [relevant files]
    endpoints:
      - method: [HTTP METHOD]
        path: [API path]
        description: [What it returns]
        auth_required: [true/false]
        response_schema:
          "200": [Success schema]
          "4xx": [Error schema]
    depends_on: []
known_limitations: []
```

## Verification

After setup, verify:
- [ ] `.testsprite/config.json` exists
- [ ] `testsprite_tests/tmp/code_summary.yaml` exists
- [ ] YAML has valid schema
```

---

## Skill 2: testsprite-generate-tests

### Purpose

Generate test plans and optionally execute them.

### Trigger

```
"generate tests"
"create test plan"
"run testsprite tests"
```

### Skill Definition

```markdown
---
name: testsprite-generate-tests
description: Generate and optionally execute TestSprite tests
---

## Prerequisites

1. TestSprite initialized (config exists)
2. Code summary exists
3. Project running on configured port (for execution)

## Workflow

### Step 1: Generate PRD (Optional)

```python
mcp__TestSprite__testsprite_generate_standardized_prd(
    projectPath="[absolute path]"
)
```

### Step 2: Generate Test Plan

For Backend:
```python
mcp__TestSprite__testsprite_generate_backend_test_plan(
    projectPath="[absolute path]"
)
```

For Frontend:
```python
mcp__TestSprite__testsprite_generate_frontend_test_plan(
    projectPath="[absolute path]"
)
```

### Step 3: Review Test Plan

Read and review:
```
testsprite_tests/testsprite_backend_test_plan.json
```

Verify test cases are sensible for your project.

### Step 4: Execute Tests (Optional)

Only if server is running:

```python
mcp__TestSprite__testsprite_generate_code_and_execute(
    projectName="[project name]",
    projectPath="[absolute path]",
    testIds=[],  # Empty = all tests
    additionalInstruction="[any special instructions]"
)
```

## Output

- Test plan: `testsprite_tests/testsprite_backend_test_plan.json`
- Test results: (varies based on execution)
```

---

## Skill 3: testsprite-maintain

### Purpose

Keep TestSprite configuration updated as project evolves.

### Trigger

```
"update testsprite config"
"refresh code summary"
"sync testsprite with changes"
```

### Skill Definition

```markdown
---
name: testsprite-maintain
description: Update TestSprite configuration for project changes
---

## When to Use

- Added new API endpoints
- Changed tech stack
- Added new features
- Modified existing features

## Workflow

### Step 1: Detect Changes

Compare current code with code summary:
```bash
# Check for new files
git diff --name-only HEAD~10

# Check for new endpoints
grep -r "@app\|@router\|@get\|@post" src/
```

### Step 2: Update Code Summary

Regenerate `testsprite_tests/tmp/code_summary.yaml`:
1. Read existing summary
2. Add new features/endpoints
3. Update tech stack if changed
4. Document new limitations

### Step 3: Regenerate Test Plan

```python
mcp__TestSprite__testsprite_generate_backend_test_plan(
    projectPath="[absolute path]"
)
```

### Step 4: Run New Tests Only

```python
mcp__TestSprite__testsprite_generate_code_and_execute(
    projectName="[project name]",
    projectPath="[absolute path]",
    testIds=["TC_NEW_1", "TC_NEW_2"],  # Only new tests
    additionalInstruction=""
)
```
```

---

## Agent Template: testsprite-orchestrator

### Purpose

Autonomous agent that manages the complete TestSprite lifecycle.

### Agent Definition

```markdown
---
name: testsprite-orchestrator
description: Agent that orchestrates TestSprite testing workflow end-to-end
---

## Capabilities

- Project type detection
- TestSprite initialization
- Code summary generation
- Test plan creation
- Test execution coordination
- Result reporting

## State Machine

```
┌───────────────┐
│ UNINITIALIZED │
└───────┬───────┘
        │ bootstrap
        ▼
┌───────────────┐
│  BOOTSTRAPPED │
└───────┬───────┘
        │ generate_summary
        ▼
┌───────────────┐
│ SUMMARY_READY │
└───────┬───────┘
        │ generate_plan
        ▼
┌───────────────┐
│  PLAN_READY   │
└───────┬───────┘
        │ execute_tests
        ▼
┌───────────────┐
│   EXECUTING   │
└───────┬───────┘
        │ report_results
        ▼
┌───────────────┐
│   COMPLETE    │
└───────────────┘
```

## Tools Used

| Tool | Purpose |
|------|---------|
| `testsprite_bootstrap` | Initialize project |
| `testsprite_generate_code_summary` | Trigger summary generation |
| `testsprite_generate_backend_test_plan` | Create test cases |
| `testsprite_generate_code_and_execute` | Run tests |
| `testsprite_open_test_result_dashboard` | View results |

## Decision Logic

### Project Type Detection

```python
if Path("package.json").exists():
    type = "frontend" if "react" in package_json else "backend"
elif Path("requirements.txt").exists() or Path("pyproject.toml").exists():
    type = "backend"
else:
    raise UnsupportedProjectError()
```

### Port Detection

```python
# Check common patterns
patterns = [
    ("Dockerfile", "EXPOSE (\\d+)"),
    ("package.json", '"port":\\s*(\\d+)'),
    (".env", "PORT=(\\d+)"),
    ("config.py", "PORT\\s*=\\s*(\\d+)"),
]

for file, pattern in patterns:
    if match := search(file, pattern):
        return int(match.group(1))

return 8000  # Default
```

## Error Handling

| Error | Recovery |
|-------|----------|
| Config exists | Skip bootstrap, proceed to summary |
| Server not running | Prompt user to start server |
| Invalid summary schema | Regenerate with template |
| Test execution failed | Open dashboard for debugging |
```

---

## Integration Patterns

### With Existing Test Frameworks

```markdown
## pytest Integration

1. Use TestSprite for test planning
2. Generate test cases as pytest functions
3. Run with pytest, not TestSprite execution

```python
# tests/test_api_testsprite.py
# Auto-generated from TestSprite plan

def test_TC001_context_pack_build_success():
    """Verify ctx build creates context_pack.json"""
    # Implementation based on test plan

def test_TC002_context_pack_build_failure():
    """Verify ctx build errors on missing _ctx/"""
    # Implementation based on test plan
```
```

### With CI/CD

```yaml
# .github/workflows/testsprite.yml
name: TestSprite Tests
on: [push, pull_request]

jobs:
  testsprite:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Start server
        run: uvicorn app:app &
      - name: Run TestSprite
        run: |
          # Claude Code MCP integration
          claude-code testsprite-generate-tests
```

---

## Anti-Patterns to Avoid

| Pattern | Why Bad | Fix |
|---------|---------|-----|
| Bootstrap on every run | Wipes config | Check `.testsprite/` first |
| Expect tool to generate summary | Tool only gives instructions | AI must write YAML |
| Use for CLI tools | Limited HTTP support | Use pytest directly |
| Skip code summary | Test plan needs it | Always generate summary first |
| Run all tests always | Slow, redundant | Use specific `testIds` |

---

## Future Enhancements

1. **Auto-detect changes** - Compare summary with code to auto-update
2. **Test result caching** - Skip passing tests
3. **Multi-project support** - Test microservices together
4. **Custom test templates** - Project-specific test patterns
