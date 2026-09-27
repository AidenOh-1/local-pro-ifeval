# Optional full evaluation paths

Default report reads only stored verdicts plus a hash-bound UID/instruction-count index. It does not need prompt text, Punkt, MLX or the private canonical core. This index is not a new reference answer and cannot rescore model outputs.

For full `score`, provide the exact original response file identified in `results/v0.1/MANIFEST.json`, every missing asset at the path/hash in `config.json`, and already-provisioned dependencies matching `requirements.lock.txt`. No automatic download is implemented. Current package intentionally fails closed with `MISSING_EVALUATION_ASSET` rather than silently substituting data/scorers. Full raw rescoring was verified for RC2, not reclassified as a fresh inference run here.

`run --dry-run` is a nonmodel input plan but still needs exact prompt data. Its missing-asset behavior is tested; successful full dry-run is not claimed for this asset-excluded package. A live `run` still uses the unchanged canonical adapter and requires separately valid core registration, resource, observation and cleanup gates. No registration is bundled or issued. Generative model calls in this task:0.

The new `report --coverage` parameter accepts only `SYNTHETIC_VERDICT_EXAMPLE`, clearly labels its output, and is not a way to override benchmark reference counts. Original full score/config bytes are hash-bound and preserved. Report/plot are standard-library paths; optional scorer imports remain inside `score`.
