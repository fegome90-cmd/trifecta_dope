### Current State
```
scripts/install_FP.py              [122 lines, pure Python]
  └─ validate_segment_structure()  [Pure domain logic]
      └─ Used by: tests/installer_test.py

tests/installer_test.py            [56 lines]
  └─ Imports from scripts/ (non-standard)
  └─ Added workaround: sys.path.insert() + pyproject.toml pythonpath
```
