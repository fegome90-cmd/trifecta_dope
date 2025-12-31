```diff
@@ -773,6 +773,9 @@ def eval_plan(
         for c in go_criteria:
             typer.echo(f"   ✓ {c}")

     telemetry.flush()
+
+    # T9.3.4: Generate confusion report
+    _generate_confusion_report(...)
+
+
+def _generate_confusion_report(
+    results: list,
+    expected_features: dict,
+    dataset_path: Path,
+    dataset_sha256: str,
+    dataset_mtime: str,
+    segment: str,
+    output_path: str
+) -> None:
+    """Generate confusion report (T9.3.4)."""
+    # Compute per-feature TP/FP/FN
+    feature_metrics = defaultdict(lambda: {"TP": 0, "FP": 0, "FN": 0})
+
+    # Track confusions (expected -> got)
+    confusions: Counter = Counter()
+    confusion_examples: dict = defaultdict(list)
+
+    for item in results:
+        expected = expected_features.get(task)
+        got = result.get("selected_feature")
+
+        if expected == "fallback":
+            if got is None:
+                feature_metrics["fallback"]["TP"] += 1
+            else:
+                feature_metrics[got]["FP"] += 1
+                confusions[(expected, got)] += 1
+        else:
+            if got == expected:
+                feature_metrics[expected]["TP"] += 1
+            elif got is None:
+                feature_metrics[expected]["FN"] += 1
+                confusions[(expected, "fallback")] += 1
+            else:
+                feature_metrics[expected]["FN"] += 1
+
