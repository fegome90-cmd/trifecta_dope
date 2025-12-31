### 2. Added Bundle Assertions

**File**: `src/application/plan_use_case.py`

- Added `_verify_bundle_assertions()` method
- Checks: paths exist, anchors found in file content
- Degradation: on failure → fallback with warning
- Telemetry: logs `bundle_assert_ok`, `bundle_assert_failed_paths[]`, `bundle_assert_failed_anchors[]`

**File**: `_ctx/aliases.yaml`

- Extended schema v2 to include `anchors[]` for each feature
- All 15 features have proper anchors matching actual file content
