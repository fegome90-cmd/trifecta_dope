# certification-harness Specification

## Purpose
Define the automated testing infrastructure to verify Trifecta installation and operation in isolated, reproducible environments.

## Requirements

### Requirement: Isolated Environment Simulation
The system MUST provide a fixture to simulate a clean machine state by isolating PATH, HOME, and Python environment.

#### Scenario: Verify Clean PATH and HOME
- GIVEN a `clean_machine` fixture
- WHEN a test is executed within the fixture
- THEN the `PATH` SHALL only contain the temporary virtual environment and essential system binaries
- AND the `HOME` directory SHALL point to a fresh temporary directory.

### Requirement: Package Installation Verification
The harness MUST verify that the Trifecta package is installable and functional when installed from a build artifact.

#### Scenario: Installation from Wheel
- GIVEN a built Trifecta wheel file
- WHEN `pip install <wheel>` is executed in the isolated environment
- THEN the `trifecta` and `trifecta-mcp` commands MUST be available in the PATH.

### Requirement: 16-Point Certification Execution
The harness SHALL automate the execution of the 16-point certification checklist.

#### Scenario: Full Certification Run
- GIVEN the certification test suite
- WHEN `pytest tests/certification` is executed
- THEN all 16 scenarios MUST pass
- AND a detailed report of each point SHALL be generated.
