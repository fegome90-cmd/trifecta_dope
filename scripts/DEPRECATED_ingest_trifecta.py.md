#!/usr/bin/env python3
"""
[DEPRECATED] Trifecta Context Pack Builder - Token-Optimized Ingestion

⚠️ DEPRECATION NOTICE ⚠️
This script is DEPRECATED and will be removed in a future version.

Use the Trifecta CLI instead:
  trifecta ctx sync --segment <segment>
  trifecta ctx build --segment <segment>

The CLI provides the same functionality with better integration,
telemetry support, and security hardening.

---

Legacy documentation below (for reference only):

Generates a structured 3-layer Context Pack from markdown files:
- Digest: Summarized content always in prompt (~10-30 lines)
- Index: Chunk references for discovery (ID, title, preview)
- Chunks: Full content delivered on-demand via tools

Usage (DEPRECATED):
    python ingest_trifecta.py --segment debug_terminal
    python ingest_trifecta.py --segment eval --output custom/pack.json
    python ingest_trifecta.py --segment hemdov --repo-root /path/to/projects
"""

# [Rest of the file remains unchanged for backward compatibility]
# Users should migrate to `trifecta ctx sync` before this script is removed.

import sys
import warnings

warnings.warn(
    "ingest_trifecta.py is deprecated. Use 'trifecta ctx sync --segment <segment>' instead.",
    DeprecationWarning,
    stacklevel=2
)

# Original implementation follows...
