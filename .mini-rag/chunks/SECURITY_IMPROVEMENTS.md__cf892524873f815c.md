#### 3.3 Python Security Checks
- **Bandit**: Static security analysis for Python code
  - Scans `src/` directory
  - Generates JSON report for artifacts
  - Severity: Low-Low threshold
- **Safety**: Checks for known vulnerabilities in dependencies
  - Uses Safety DB for vulnerability lookup
  - JSON output for tracking
