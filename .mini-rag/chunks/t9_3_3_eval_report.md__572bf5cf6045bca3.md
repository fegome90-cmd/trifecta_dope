```diff
--- a/src/application/plan_use_case.py
+++ b/src/application/plan_use_case.py
@@ -169,47 +169,118 @@ class PlanUseCase:

     def _match_l2_nl_triggers(
         self, task: str, features: dict
-    ) -> tuple[str | None, str | None]:
-        """L2: Direct NL trigger match (canonical intent phrases).
+    ) -> tuple[str | None, str | None, str | None, int, str | None]:
+        """L2: Direct NL trigger match with improved scoring and guardrails (T9.3.3).

         Returns:
-            (feature_id, matched_trigger) or (None, None)
+            (feature_id, matched_trigger, warning, score, match_mode)
+            - warning: Warning string or None (ambiguous_single_word_triggers | match_tie_fallback)
+            - score: Match score (2=exact, 1=subset, 0=no match)
+            - match_mode: "exact" | "subset" | None
         """
         nl_ngrams = self._normalize_nl(task)
+        task_tokens = self._tokenize(task)

-        best_match = None
-        best_trigger = None
-        best_priority = 0
+        candidates = []
+        single_word_hits = []

         for feature_id in sorted(features.keys()):
             # ... trigger matching ...
+            # Exact match in ngrams (score=2)
             if trigger_lower in nl_ngrams:
-                if priority > best_priority:
-                    best_match = feature_id
-                    best_trigger = trigger
-
