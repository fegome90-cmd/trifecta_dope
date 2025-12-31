else:
+                feature_metrics[expected]["FN"] += 1
+                feature_metrics[got]["FP"] += 1
+                confusions[(expected, got)] += 1
+
+    # Build markdown report with:
+    # - Dataset identity (SHA256, mtime, path)
+    # - Run identity (commit hash, timestamp, segment)
+    # - Per-feature TP/FP/FN with precision/recall/F1
+    # - Top 10 confusion pairs with example task IDs
+    # - Save to docs/plans/t9_3_4_confusions.md
```
