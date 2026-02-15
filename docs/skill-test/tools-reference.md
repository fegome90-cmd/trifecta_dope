# TestSprite MCP Tools Reference

> Detailed documentation for each TestSprite MCP tool

---

## testsprite_bootstrap

**Purpose**: First-time project initialization

### When to Use
- Starting a new TestSprite project
- No `.testsprite/config.json` exists

### When NOT to Use
- Config already exists (will error/wipe)
- Project type is CLI-only (limited support)

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `localPort` | int | Yes | Port where app runs (1-65535) |
| `type` | enum | Yes | "frontend" or "backend" |
| `projectPath` | string | Yes | Absolute path to project root |
| `testScope` | enum | Yes | "codebase" or "diff" |
| `pathname` | string | No | Webpage path (default: empty) |

### Example Call

```python
mcp__TestSprite__testsprite_bootstrap(
    localPort=8000,
    type="backend",
    projectPath="/Users/dev/myproject",
    testScope="codebase"
)
```

### Output

```json
{
  "next_action": [
    "The project is not running on port 8000. Please start the project.",
    "AI assistant will call testsprite_generate_code_summary..."
  ]
}
```

### Workflow Notes

1. Check if `.testsprite/config.json` exists first
2. If exists, skip bootstrap and proceed to code summary
3. Bootstrap expects a running server for frontend testing
4. For CLI tools, test execution may not work as expected

---

## testsprite_generate_code_summary

**Purpose**: Analyze codebase and extract tech stack, features, and endpoints

### Key Insight

**This tool does NOT generate the summary itself.** It returns instructions for the AI to generate the YAML file.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `projectRootPath` | string | Yes | Absolute path to project root |

### Expected AI Output

The AI must generate a YAML file at:
```
{projectPath}/testsprite_tests/tmp/code_summary.yaml
```

### YAML Schema

```yaml
version: "2"
type: backend
tech_stack:
  - Python 3.12
  - FastAPI
  - PostgreSQL
features:
  - name: Feature Name
    description: What this feature does
    files:
      - src/module/file.py
    endpoints:
      - method: GET
        path: /api/resource
        description: Get resource
        auth_required: false
        response_schema:
          "200": Resource
          "400": Error
    depends_on:
      - Authentication
known_limitations:
  - issue: Description of limitation
    location: src/file.py
    impact: What this affects
```

### Field Rules

- `version`: Must be "2"
- `type`: Must be "backend" or "frontend"
- `features`: Array of feature objects
  - Each feature must include `endpoints` with `method`, `path`, `description`, `auth_required`
- `known_limitations`: Array of issues (can be empty `[]`)

---

## testsprite_generate_standardized_prd

**Purpose**: Generate a Product Requirements Document

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `projectPath` | string | Yes | Absolute path to project root |

### Behavior

Returns next action to call `testsprite_generate_backend_test_plan` or `testsprite_generate_frontend_test_plan`.

---

## testsprite_generate_backend_test_plan

**Purpose**: Generate test case definitions for backend APIs

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `projectPath` | string | Yes | Absolute path to project root |

### Output

Creates file at:
```
{projectPath}/testsprite_tests/testsprite_backend_test_plan.json
```

### Test Plan Format

```json
[
  {
    "id": "TC001",
    "title": "test_endpoint_name_success",
    "description": "Verify that calling endpoint X with valid params returns Y."
  },
  {
    "id": "TC002",
    "title": "test_endpoint_name_failure",
    "description": "Verify that calling endpoint X with invalid params returns error."
  }
]
```

### Example Generated Test Cases

| ID | Title | Description |
|----|-------|-------------|
| TC001 | test_context_pack_build_success | Verify ctx build creates context_pack.json |
| TC002 | test_context_pack_build_failure | Verify ctx build errors on missing _ctx/ |
| TC003 | test_context_search_with_results | Verify search returns chunk IDs |
| TC004 | test_context_search_no_results | Verify search handles no matches |

---

## testsprite_generate_code_and_execute

**Purpose**: Generate test code and run it

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `projectName` | string | Yes | - | Root directory name |
| `projectPath` | string | Yes | - | Absolute path to root |
| `testIds` | array | No | [] | Specific test IDs (empty = all) |
| `additionalInstruction` | string | No | "" | Extra instructions |

### Prerequisites

1. Project must be running on specified port
2. Test plan must exist
3. Code summary must exist

### Workflow

1. Reads test plan JSON
2. Generates test code (Python/JS based on project)
3. Executes tests against running server
4. Returns results

---

## testsprite_rerun_tests

**Purpose**: Re-run previously executed tests

### Use Case
- After fixing code issues
- After updating test configuration
- Regression testing

---

## testsprite_open_test_result_dashboard

**Purpose**: Open interactive dashboard to review/debug test results

### Use Case
- Analyze test failures
- Debug test issues
- View detailed execution logs

---

## Tool Execution Order

```
1. testsprite_bootstrap          (once per project)
         │
         ▼
2. testsprite_generate_code_summary (AI generates YAML)
         │
         ▼
3. testsprite_generate_standardized_prd
         │
         ▼
4. testsprite_generate_backend_test_plan
         │
         ▼
5. testsprite_generate_code_and_execute
         │
         ▼
6. testsprite_rerun_tests (optional)
   testsprite_open_test_result_dashboard (optional)
```

---

## Common Patterns

### Starting a New Project

```python
# 1. Bootstrap
mcp__TestSprite__testsprite_bootstrap(
    localPort=8000,
    type="backend",
    projectPath="/path/to/project",
    testScope="codebase"
)

# 2. Generate code summary (AI task)
# Write YAML to testsprite_tests/tmp/code_summary.yaml

# 3. Generate test plan
mcp__TestSprite__testsprite_generate_backend_test_plan(
    projectPath="/path/to/project"
)

# 4. Execute tests
mcp__TestSprite__testsprite_generate_code_and_execute(
    projectName="myproject",
    projectPath="/path/to/project",
    testIds=[],
    additionalInstruction=""
)
```

### Running Specific Tests

```python
# Only run TC001 and TC002
mcp__TestSprite__testsprite_generate_code_and_execute(
    projectName="myproject",
    projectPath="/path/to/project",
    testIds=["TC001", "TC002"],
    additionalInstruction="Focus on error handling"
)
```
