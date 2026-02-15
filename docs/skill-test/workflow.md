# TestSprite MCP Workflow Guide

> Step-by-step guide for using TestSprite MCP

---

## Prerequisites

- [ ] Project has a running server (for web testing)
- [ ] MCP server is configured and accessible
- [ ] Project type is supported (backend/frontend)

---

## Workflow Overview

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Bootstrap  │────▶│  Code Summary │────▶│  Test Plan  │
└─────────────┘     │   (AI Task)   │     └─────────────┘
                    └──────────────┘            │
                                                ▼
                    ┌──────────────┐     ┌─────────────┐
                    │    Rerun     │◀────│   Execute   │
                    │   (Optional) │     │   Tests     │
                    └──────────────┘     └─────────────┘
```

---

## Step 1: Check Existing Configuration

Before starting, check if TestSprite is already configured:

```bash
# Check for existing config
ls -la .testsprite/config.json

# If exists, skip to Step 3
```

---

## Step 2: Bootstrap (First Time Only)

### For Backend Projects

```python
mcp__TestSprite__testsprite_bootstrap(
    localPort=8000,           # Port your API runs on
    type="backend",
    projectPath="/absolute/path/to/project",
    testScope="codebase"      # or "diff" for changed files only
)
```

### For Frontend Projects

```python
mcp__TestSprite__testsprite_bootstrap(
    localPort=3000,           # Port your app runs on
    type="frontend",
    projectPath="/absolute/path/to/project",
    testScope="codebase",
    pathname="/"              # Optional: specific page path
)
```

### Expected Response

```json
{
  "next_action": [
    "The project is not running on port 8000. Please start the project.",
    "Call testsprite_generate_code_summary..."
  ]
}
```

---

## Step 3: Generate Code Summary

**This is an AI task** - the tool returns instructions, not the summary.

### Call the Tool

```python
mcp__TestSprite__testsprite_generate_code_summary(
    projectRootPath="/absolute/path/to/project"
)
```

### AI Task: Create the YAML

The AI must analyze the codebase and write to:
```
{projectPath}/testsprite_tests/tmp/code_summary.yaml
```

#### Template

```yaml
version: "2"
type: backend  # or frontend
tech_stack:
  - Language
  - Framework
  - Database
  - Other dependencies
features:
  - name: Feature Name
    description: What it does
    files:
      - src/path/to/file.py
    endpoints:
      - method: GET
        path: /api/resource
        description: Get resource
        auth_required: false
        response_schema:
          "200": SuccessResponse
          "400": ErrorResponse
    depends_on:
      - Other Feature
known_limitations:
  - issue: Description
    location: src/file.py
    impact: Effect
```

### Analysis Tips

1. **For Backend**: Focus on API endpoints, request/response schemas
2. **For Frontend**: Focus on user flows, UI components
3. **Include auth**: Note which endpoints require authentication
4. **List dependencies**: Features often depend on others

---

## Step 4: Generate PRD (Optional)

```python
mcp__TestSprite__testsprite_generate_standardized_prd(
    projectPath="/absolute/path/to/project"
)
```

This chains automatically to test plan generation.

---

## Step 5: Generate Test Plan

### Backend Test Plan

```python
mcp__TestSprite__testsprite_generate_backend_test_plan(
    projectPath="/absolute/path/to/project"
)
```

### Frontend Test Plan

```python
mcp__TestSprite__testsprite_generate_frontend_test_plan(
    projectPath="/absolute/path/to/project"
)
```

### Output File

```
testsprite_tests/testsprite_backend_test_plan.json
```

### Test Plan Structure

```json
[
  {
    "id": "TC001",
    "title": "test_endpoint_success_case",
    "description": "Verify X returns Y"
  },
  {
    "id": "TC002",
    "title": "test_endpoint_failure_case",
    "description": "Verify X handles errors"
  }
]
```

---

## Step 6: Execute Tests

### Prerequisites

- [ ] Server running on specified port
- [ ] Test plan exists
- [ ] Code summary exists

### Run All Tests

```python
mcp__TestSprite__testsprite_generate_code_and_execute(
    projectName="myproject",
    projectPath="/absolute/path/to/project",
    testIds=[],  # Empty = all tests
    additionalInstruction=""
)
```

### Run Specific Tests

```python
mcp__TestSprite__testsprite_generate_code_and_execute(
    projectName="myproject",
    projectPath="/absolute/path/to/project",
    testIds=["TC001", "TC003"],  # Only these
    additionalInstruction="Focus on error handling edge cases"
)
```

### With Additional Instructions

```python
additionalInstruction = """
- Test boundary conditions
- Include timeout scenarios
- Verify error messages are user-friendly
"""
```

---

## Step 7: Review Results

### Open Dashboard

```python
mcp__TestSprite__testsprite_open_test_result_dashboard()
```

### Re-run Failed Tests

```python
mcp__TestSprite__testsprite_rerun_tests()
```

---

## Common Scenarios

### Scenario 1: New Feature Testing

```python
# 1. Update code summary with new feature
# 2. Regenerate test plan
mcp__TestSprite__testsprite_generate_backend_test_plan(projectPath=...)

# 3. Run tests for new feature only
mcp__TestSprite__testsprite_generate_code_and_execute(
    projectName="project",
    projectPath=...,
    testIds=["TC010", "TC011"],  # New test IDs
    additionalInstruction=""
)
```

### Scenario 2: Regression Testing

```python
# Run all tests after changes
mcp__TestSprite__testsprite_generate_code_and_execute(
    projectName="project",
    projectPath=...,
    testIds=[],
    additionalInstruction="Verify no regressions in existing functionality"
)
```

### Scenario 3: CLI Tool (Limited Support)

For CLI tools, TestSprite can generate test plans but execution differs:

1. Generate code summary (mark as CLI tool)
2. Generate test plan
3. **Manual execution** - use pytest or shell tests instead
4. Report results manually

---

## Troubleshooting

### "Project not running on port"

Start your server:
```bash
# Backend
uvicorn app:app --port 8000

# Frontend
npm run dev
```

### "Config already exists"

Skip bootstrap:
```python
# Don't call testsprite_bootstrap if .testsprite/config.json exists
# Proceed directly to code summary
```

### "Code summary not found"

Ensure AI generated the file:
```bash
ls -la testsprite_tests/tmp/code_summary.yaml
```

### "Test plan generation failed"

Verify code summary format:
- `version: "2"`
- `type: backend|frontend`
- `features` array with endpoints

---

## Best Practices

1. **Keep code summary updated** - Regenerate when adding features
2. **Use specific test IDs** - Don't always run all tests
3. **Add instructions** - Guide test generation with context
4. **Review test plans** - Verify generated tests make sense
5. **Iterate** - Use `additionalInstruction` to improve coverage
