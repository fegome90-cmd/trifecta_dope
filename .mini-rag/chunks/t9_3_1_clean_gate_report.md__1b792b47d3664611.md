### Implementation

Bundle assertions were implemented in `plan_use_case.py` with the following logic:

```python
def _verify_bundle_assertions(self, feature_id: str, bundle: dict, target_path: Path):
    failed_paths = []
    failed_anchors = []

    for path_str in bundle.get("paths", []):
        path = target_path / path_str
        if not path.exists():
            failed_paths.append(path_str)

    for anchor in bundle.get("anchors", []):
        anchor_found = False
        for path_str in bundle.get("paths", []):
            path = target_path / path_str
            if path.exists():
                if anchor in path.read_text():
                    anchor_found = True
                    break
        if not anchor_found:
            failed_anchors.append(anchor)

    return len(failed_paths) == 0 and len(failed_anchors) == 0
```
