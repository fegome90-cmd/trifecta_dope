### Degradation Behavior

When bundle assertions fail:
- Feature match is **NOT** returned
- Degrades to **fallback** (L3)
- Warning reason: `"bundle_assert_failed"`
- Telemetry logs: `bundle_assert_ok: false`, `bundle_assert_failed_paths[]`, `bundle_assert_failed_anchors[]`
