### Phase 2: Update Imports (10 min)

```
scripts/install_trifecta_context.py:
  OLD: from install_FP import validate_segment
  NEW: from src.infrastructure.validators import validate_segment_structure

  Update function call:
    OLD: validate_segment(path)
    NEW: validate_segment_structure(path).valid
```

```
tests/installer_test.py:
  OLD: sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
       from install_FP import validate_segment_structure
  NEW: from src.infrastructure.validators import validate_segment_structure
```
