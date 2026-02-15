# TestSprite MCP Documentation

> Reverse-engineered documentation for the TestSprite MCP server

## Overview

TestSprite MCP is an AI-assisted testing tool that generates and executes tests for backend APIs and frontend applications. It uses a multi-step workflow to analyze codebases, create test plans, and run tests.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    TestSprite MCP Server                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  bootstrap   │───▶│ code_summary │───▶│     prd      │  │
│  │              │    │    (AI gen)  │    │              │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│                                                │             │
│                                                ▼             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │    rerun     │◀───│   execute    │◀───│  test_plan   │  │
│  │              │    │              │    │  (generated) │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Key Concepts

### 1. Bootstrap Phase
- **Purpose**: Initialize TestSprite for a project
- **Requires**: Project path, type (frontend/backend), local port
- **Creates**: `.testsprite/config.json` (if not exists)
- **Note**: Only run once per project

### 2. Code Summary (AI-Generated)
- **Purpose**: Document project structure and features
- **Format**: YAML with specific schema
- **AI Responsibility**: The AI assistant must generate this file
- **Output**: `testsprite_tests/tmp/code_summary.yaml`

### 3. Test Plan Generation
- **Backend**: Creates test cases for API endpoints
- **Frontend**: Creates test cases for UI interactions
- **Output**: `testsprite_tests/testsprite_backend_test_plan.json`

### 4. Test Execution
- **Generates**: Test code based on test plan
- **Executes**: Runs tests against running server
- **Reports**: Results via dashboard

## Supported Project Types

| Type | Requirements | Test Focus |
|------|--------------|------------|
| Backend | Running server on port | API endpoints, CRUD operations |
| Frontend | Running app on port | UI interactions, component tests |

## Limitations

1. **Web-Centric**: Designed for HTTP-based testing
2. **Server Required**: Needs running server for execution
3. **CLI Tools**: Limited support for non-HTTP CLIs
4. **AI Dependency**: Code summary must be AI-generated

## Files Generated

```
testsprite_tests/
├── tmp/
│   └── code_summary.yaml       # AI-generated code summary
├── testsprite_backend_test_plan.json  # Test case definitions
└── (test execution results)
```

## Exploration Results (2026-02-15)

Tested on two projects with different architectures:

| Project | Type | Bootstrap | Plan | Execution | Results |
|---------|------|-----------|------|-----------|---------|
| trifecta_dope | CLI (Typer) | ✅ | ✅ | ❌ No HTTP | N/A |
| raycast_ext | Backend (FastAPI) | ✅ | ✅ | ✅ | 1/10 passed |

### Key Finding: Tunnel Architecture

TestSprite creates a tunnel to your local server. This enables cloud-based test execution but **requires a running HTTP server**.

```
Local Server (port 8000)
        ↕
    Tunnel (TestSprite infrastructure)
        ↕
  Test Execution (cloud)
```

### Test Failure Analysis

9 of 10 tests failed on raycast_ext due to:
- Pydantic validation errors (422) vs expected HTTP codes
- Schema mismatches between test requests and API
- Tests cannot simulate degraded/unavailable states easily

**Recommendation**: Use TestSprite for test planning, then refine tests based on actual API behavior.

## See Also

- [Tools Reference](tools-reference.md) - Detailed tool documentation
- [Workflow Guide](workflow.md) - Step-by-step usage
- [Findings](findings.md) - Key discoveries (updated with execution results)
- [CLI Workaround](cli-workaround.md) - Testing CLI tools with pytest
