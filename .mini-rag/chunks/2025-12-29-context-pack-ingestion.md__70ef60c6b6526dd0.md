## Problem Statement

Current approaches to loading context for code agents have two fundamental issues:

1. **Inject full markdown** → Burns tokens on every call, doesn't scale
2. **Unstructured context** → No index, no way to request specific chunks

**Solution**: 3-layer Context Pack (Digest + Index + Chunks) delivered on-demand via tools.

---
