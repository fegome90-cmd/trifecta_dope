best_match = feature_id
-                    best_trigger = trigger
-                    best_priority = priority
+                score = 2
+                match_mode = "exact"
+            # Subset match: all trigger words present (score=1)
+            elif trigger_words.issubset(task_tokens):
+                score = 1
+                match_mode = "subset"
+
+            if score > 0:
+                candidates.append((feature_id, trigger, score, priority, match_mode))
+                if is_single_word:
+                    single_word_hits.append((feature_id, trigger_lower))
+
+        # Single-word guardrail (T9.3.3)
+        if is_single_word:
+            if priority < 4:
+                continue  # Skip low-priority single-word triggers
+            if other_single_word_hits:
+                return None, None, "ambiguous_single_word_triggers", 0, None
+
+        # Sort by (score desc, priority desc)
+        filtered_candidates.sort(key=lambda x: (x[2], x[3]), reverse=True)
+
+        # Check for ties
+        if ties:
+            return None, None, "match_tie_fallback", 0, None
+
+        return best_feature, best_trigger, warning, best_score, best_match_mode
```
