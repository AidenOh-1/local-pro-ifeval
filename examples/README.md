# Synthetic usage example — not a benchmark measurement

Two handcrafted verdict records show reporting only. No model generated these.
Expected strict prompt 1/2, strict instruction 2/3, loose prompt 2/2,
loose instruction 3/3. These records are never combined with the 541 results.

```sh
PYTHONPATH=src python3 -B -m local_pro_release report --scores examples/verdicts.json --coverage examples/coverage.json --output out/example
```
