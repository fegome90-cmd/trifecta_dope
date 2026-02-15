# TestSprite MCP Findings

> Key discoveries from reverse-engineering the TestSprite MCP server

---

## Critical Findings

### 1. AI-Generated Code Summary

**Discovery**: The `testsprite_generate_code_summary` tool does NOT generate the summary itself.

**Implication**: The AI assistant must:
1. Analyze the codebase
2. Generate YAML following a specific schema
3. Write to `testsprite_tests/tmp/code_summary.yaml`

**Why This Matters**:
- This is a design pattern where MCP tools delegate work to AI
- The tool is more of a "task router" than a generator
- AI must understand project structure deeply

### 2. Web-Centric Architecture (CONFIRMED)

**Discovery**: TestSprite is designed PRIMARILY for HTTP-based testing.

**Evidence**:
- `localPort` parameter required for bootstrap
- Tool prompts to "start the project" on a port
- Test cases are endpoint-focused
- Frontend testing assumes browser interactions

**EXECUTION CONFIRMED** (2026-02-15):
```
checkPortListening error: 8000 localhost
checkPortListening failed: 8000 localhost
❌ Test execution failed: Error: Failed to generate and execute tests:
Error: Failed to set up testing tunnel: Because the local project
is not running on port 8000.
```

**Root Cause**: TestSprite creates a **tunnel** to communicate with the local server. Without a running HTTP server, the tunnel cannot be established.

**Implication for CLI Tools**:
- ✅ Test plan generation works (based on code summary)
- ❌ Test execution REQUIRES running HTTP server
- ✅ Use TestSprite for planning, manual pytest for CLI execution

### 3. Chained Tool Workflow

**Discovery**: Tools chain automatically via `next_action` responses.

**Pattern**:
```json
{
  "next_action": [
    "Message to user/AI",
    { "type": "tool_use", "tool": "next_tool_name" }
  ]
}
```

**Workflow Chain**:
```
bootstrap → code_summary → prd → test_plan → execute
```

### 4. Test Plan Structure

**Discovery**: Test plans use a simple JSON format.

**Generated Test Plan Example**:
```json
[
  {
    "id": "TC001",
    "title": "test_context_pack_build_success",
    "description": "Verify that running 'trifecta ctx build'..."
  }
]
```

**Pattern**:
- Success/failure pairs (TC001 success, TC002 failure)
- Named with `test_<feature>_<outcome>` convention
- Descriptions focus on verification, not implementation

### 5. Schema Requirements

**Discovery**: Code summary YAML has strict requirements.

**Required Fields**:
```yaml
version: "2"  # Must be exactly "2"
type: backend | frontend  # Must be one of these

features:
  - name: string
    description: string
    files: [string]
    endpoints:
      - method: HTTP_METHOD
        path: /api/path
        description: string
        auth_required: boolean
        response_schema: object
    depends_on: [string]

known_limitations: [object]  # Can be empty array
```

---

## Tool Behavior Details

### testsprite_bootstrap

| Aspect | Finding |
|--------|---------|
| Idempotency | NOT idempotent - check for existing config first |
| Prerequisite | Server should be running (for frontend) |
| Output | Instructions, not files |
| Error Handling | Returns messages in `next_action` array |

### testsprite_generate_code_summary

| Aspect | Finding |
|--------|---------|
| Output | Instructions for AI, not the summary itself |
| AI Task | Must write to `testsprite_tests/tmp/code_summary.yaml` |
| Schema | Strict YAML format required |
| Scope | Covers tech_stack, features, endpoints, limitations |

### testsprite_generate_backend_test_plan

| Aspect | Finding |
|--------|---------|
| Input | Reads `code_summary.yaml` |
| Output | `testsprite_backend_test_plan.json` |
| Content | Test case definitions with ID, title, description |
| Coverage | Generates success and failure cases |

---

## Anti-Patterns Identified

### 1. Calling Bootstrap Multiple Times

```python
# BAD: Calling bootstrap when config exists
mcp__TestSprite__testsprite_bootstrap(...)  # May wipe config!

# GOOD: Check first
if not Path(".testsprite/config.json").exists():
    mcp__TestSprite__testsprite_bootstrap(...)
```

### 2. Expecting Tool to Generate Summary

```python
# BAD: Expecting tool to return summary
result = mcp__TestSprite__testsprite_generate_code_summary(...)
# result is just instructions, not the summary!

# GOOD: Generate YAML yourself based on instructions
# (AI task to write the file)
```

### 3. CLI Tool Testing

```python
# BAD: Expecting full test execution for CLI
# TestSprite designed for HTTP testing

# GOOD: Use TestSprite for planning, then:
# - Write pytest tests manually
# - Use subprocess testing
# - Focus on CLI output verification
```

---

## File Structure Created

```
project/
├── .testsprite/
│   └── config.json              # Created by bootstrap
│
└── testsprite_tests/
    ├── tmp/
    │   └── code_summary.yaml    # AI-generated summary
    │
    └── testsprite_backend_test_plan.json  # Generated test cases
```

---

## Comparison: TestSprite vs Traditional Testing

| Aspect | TestSprite MCP | Traditional |
|--------|---------------|-------------|
| Test Generation | AI-assisted | Manual |
| Code Analysis | AI + YAML schema | Manual review |
| Test Plan | Auto-generated | Manual design |
| Execution | MCP-driven | pytest/jest/etc |
| Scope | Web-focused | Any type |
| Learning Curve | Moderate | Low |

---

## Recommendations for Future Skill/Agent Creation

### Skill Template: TestSprite Backend Testing

```markdown
---
name: testsprite-backend
description: Use when setting up automated testing for backend APIs
---

## Workflow

1. Check for `.testsprite/config.json`
2. If missing, call `testsprite_bootstrap`
3. Analyze codebase, generate `code_summary.yaml`
4. Generate test plan
5. Execute tests

## Code Summary Template
[YAML template here]

## Anti-Patterns
- Don't call bootstrap twice
- Don't use for CLI tools
```

### Agent Template: TestSprite Orchestrator

```markdown
---
name: testsprite-orchestrator
description: Agent that coordinates TestSprite testing workflow
---

## Responsibilities

1. Detect project type (backend/frontend/CLI)
2. Check existing TestSprite state
3. Generate/refresh code summary
4. Manage test execution
5. Report results

## State Machine

```
UNINITIALIZED → BOOTSTRAPPED → SUMMARY_READY → PLAN_READY → EXECUTING → COMPLETE
```
```

---

### 6. Tunnel-Based Architecture (NEW)

**Discovery**: TestSprite uses a tunnel to connect to local servers.

**Evidence from execution**:
```
Error occurred. Cleaning up tunnel...
HTTP Proxy has been closed.
Tunnel has been closed.
```

**Implications**:
- Local server MUST be running on configured port
- TestSprite proxies requests through its infrastructure
- This enables cloud-based test execution against local code
- Security consideration: data flows through TestSprite servers

---

## Open Questions (Updated with Answers)

1. **How does frontend test execution work?**
   - Likely uses Playwright/Puppeteer through the tunnel
   - UI interactions specified in generated test code
   - ✅ ANSWERED: Requires running dev server

2. **What test framework does execution use?**
   - Appears to generate custom test code
   - Executes through TestSprite's infrastructure
   - ❓ Still unclear - may be proprietary

3. **How are auth tokens handled?**
   - Configured in code summary `auth_required` field
   - Likely passed through tunnel headers
   - ❓ Implementation details unknown

4. **What's the dashboard experience?**
   - `testsprite_open_test_result_dashboard` tool available
   - Likely opens browser to TestSprite service
   - ❓ Not tested (no successful execution)

5. **NEW: Can CLI tools use TestSprite?**
   - ✅ ANSWERED: Only for planning phase
   - ❌ Execution requires HTTP server
   - Workaround: Convert test plan to pytest manually

---

## Session Metadata

| Field | Value |
|-------|-------|
| Date | 2026-02-15 |
| Projects Tested | trifecta_dope (CLI), raycast_ext (FastAPI) |
| TestSprite Version | MCP via npx |
| Tools Explored | 8 of 8 (all tools used) |
| Documentation Created | 6 files |
| Execution Results | CLI: ❌ Failed, FastAPI: ✅ Executed (1/10 passed) |

---

## Project Comparison: CLI vs FastAPI

| Aspect | trifecta_dope (CLI) | raycast_ext (FastAPI) |
|--------|---------------------|----------------------|
| Project Type | CLI (Typer) | Backend (FastAPI) |
| HTTP Server | ❌ No | ✅ Yes (port 8000) |
| Bootstrap | ✅ Success | ✅ Success |
| Code Summary | ✅ Generated | ✅ Generated |
| Test Plan | ✅ 10 tests | ✅ 10 tests |
| **Execution** | ❌ Failed (no server) | ✅ Executed via tunnel |
| Results | N/A | 1 passed, 9 failed |

---

## Test Execution Results (raycast_ext)

### Summary

| Metric | Value |
|--------|-------|
| Total Tests | 10 |
| ✅ Passed | 1 (10%) |
| ❌ Failed | 9 (90%) |

### Test Results Detail

| ID | Endpoint | Expected | Actual | Status |
|----|----------|----------|--------|--------|
| TC001 | POST /api/v1/improve-prompt | 200 | 422 | ❌ |
| TC002 | POST /api/v1/improve-prompt (empty) | 400 | 422 | ❌ |
| TC003 | POST /api/v1/improve-prompt (no LLM) | 503 | 422 | ❌ |
| TC004 | GET /health | 200 | 200 | ✅ |
| TC005 | GET /health (degraded) | 'degraded' | 'healthy' | ❌ |
| TC006 | GET /health (unavailable) | 503 | 200 | ❌ |
| TC007 | GET /api/v1/metrics/summary | 200 | 400 | ❌ |
| TC008 | GET /api/v1/metrics/summary (no DB) | 503 | 400 | ❌ |
| TC009 | GET /api/v1/metrics/trends | 200 | 400 | ❌ |
| TC010 | GET /api/v1/metrics/trends (invalid) | 400 + error | No error | ❌ |

### Failure Analysis

**Pattern**: Most failures involve Pydantic validation errors (422) instead of expected HTTP codes.

**Root Causes**:
1. **Request schema mismatch**: Tests send different payloads than API expects
2. **Validation-first design**: API validates before checking business conditions
3. **Mocking limitations**: Tests can't easily simulate degraded/unavailable states

**Generated Test Code Pattern**:
```python
import requests

def test_post_api_v1_improve_prompt_valid_input():
    response = requests.post(
        "http://localhost:8000/api/v1/improve-prompt",
        json={"idea": "test idea", "context": "test context"}
    )
    assert response.status_code == 200
```

### 7. Test Code Generation (NEW)

**Discovery**: TestSprite generates Python test code using `requests` library.

**Generated Code Characteristics**:
- Uses `requests` for HTTP calls
- Simple assertion patterns
- No test framework (raw Python functions)
- Executed via TestSprite infrastructure

**Example from raycast_ext**:
```python
def test_get_health_check_healthy_status():
    """Test the GET /health endpoint..."""
    response = requests.get("http://localhost:8000/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
```

### 8. Dashboard Links (NEW)

**Discovery**: Each test generates a unique dashboard URL for visualization.

**Pattern**:
```
https://www.testsprite.com/dashboard/mcp/tests/{test-id}/{run-id}
```

**Example**:
```
https://www.testsprite.com/dashboard/mcp/tests/37744638-41c8-43b1-9a5d-b4ef73fad01c/23ecc4ac-f10e-4c95-a2a6-6f634dce1ddc
```

**Usage**: Use `testsprite_open_test_result_dashboard` to open interactive review.

---

## Test Plans Generated

### trifecta_dope (CLI - Not Executed)

TestSprite created 10 test cases for CLI commands:

| ID | Test Case | Description |
|----|-----------|-------------|
| TC001 | test_context_pack_build_success | Verify ctx build creates context_pack.json |
| TC002 | test_context_pack_build_failure | Verify ctx build errors on missing _ctx/ |
| TC003 | test_context_pack_validate_success | Validate passes on valid pack |
| TC004 | test_context_pack_validate_failure | Validate fails on corrupted pack |
| TC005 | test_context_pack_sync_success | Sync completes successfully |
| TC006 | test_context_pack_sync_failure | Sync fails appropriately |
| TC007 | test_context_search_with_results | Search returns chunk IDs |
| TC008 | test_context_search_no_results | Search handles zero results |
| TC009 | test_context_get_chunk_content_success | Get returns content |
| TC010 | test_context_get_chunk_content_not_found | Get errors on invalid IDs |

**Recommendation**: Convert to pytest tests manually using `subprocess` module.

### raycast_ext (FastAPI - Executed)

TestSprite created 10 test cases for API endpoints:

| ID | Test Case | Result |
|----|-----------|--------|
| TC001 | post_api_v1_improve_prompt_valid_input | ❌ Expected 200, got 422 |
| TC002 | post_api_v1_improve_prompt_empty_idea | ❌ Expected 400, got 422 |
| TC003 | post_api_v1_improve_prompt_llm_unavailable | ❌ Expected 503, got 422 |
| TC004 | get_health_check_healthy_status | ✅ PASSED |
| TC005 | get_health_check_degraded_status | ❌ Expected 'degraded', got 'healthy' |
| TC006 | get_health_check_service_unavailable | ❌ Expected 503, got 200 |
| TC007 | get_api_v1_metrics_summary_success | ❌ Expected 200, got 400 |
| TC008 | get_api_v1_metrics_summary_db_missing | ❌ Expected 503, got 400 |
| TC009 | get_api_v1_metrics_trends_valid_days | ❌ 400 Bad Request |
| TC010 | get_api_v1_metrics_trends_invalid_days | ❌ Missing error field |

---

## Recommendations

### For API Development

1. **Validate schema alignment**: Compare test request payloads with actual API schemas
2. **Review error codes**: Ensure 400/422/503 usage matches test expectations
3. **Add state simulation**: Provide endpoints or config to simulate degraded states

### For TestSprite Usage

1. **Use for planning first**: Generate test plans to understand coverage
2. **Execute on FastAPI**: Best results with HTTP backends
3. **Review generated code**: Check dashboard URLs for detailed analysis
4. **Handle validation errors**: 422 often indicates schema mismatch, not bug
