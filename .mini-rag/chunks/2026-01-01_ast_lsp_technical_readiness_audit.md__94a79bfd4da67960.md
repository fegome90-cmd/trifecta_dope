## 4. Root Cause Analysis
The PR likely focused on "getting the classes written" (T1, T4, T5) but skipped the "application layer" (T3, T7) entirely. The tests passed because they tested the *classes in isolation*, not the *app*.
