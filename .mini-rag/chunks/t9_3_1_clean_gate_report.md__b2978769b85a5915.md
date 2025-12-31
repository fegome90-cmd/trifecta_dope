### The Tension

The gate criteria create a mathematical tension for a well-performing system:

- To achieve **< 20% fallback**, maximum 7 tasks can fall back (40 × 0.20 = 8)
- To achieve **<= 70% alias**, maximum 28 tasks can match via alias (40 × 0.70 = 28)
- With 7 fallbacks, 33 tasks match via alias → 82.5% alias rate ✗
- To achieve 70% alias rate, 12 tasks would need to fall back → 30% fallback rate ✗
