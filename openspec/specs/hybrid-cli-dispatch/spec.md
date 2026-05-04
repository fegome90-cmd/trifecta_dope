# hybrid-cli-dispatch Specification

## Purpose
Achieve near-zero latency for CLI operations by routing commands through a running daemon process.

## Requirements

### Requirement: Automatic Daemon Detection
The CLI MUST check for an active daemon via a local Unix socket before executing operations locally.

#### Scenario: Route to daemon
- GIVEN an active F1 daemon
- WHEN the user runs `trifecta ctx search`
- THEN the CLI SHALL forward the request to the daemon socket
- AND return results without a fresh Python/Index bootstrap.

### Requirement: Seamless Local Fallback
The system MUST fallback to local execution if the daemon is unreachable.

#### Scenario: Daemon offline
- GIVEN no running daemon
- WHEN a CLI command is executed
- THEN the system SHALL fallback to local UseCase execution with a 1-second timeout warning.
