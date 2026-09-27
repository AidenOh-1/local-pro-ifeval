# Historical context, not matched performance

The [pinned DeepSeek-V3 README](https://github.com/deepseek-ai/DeepSeek-V3/blob/9b4e9788e4a3a731f7567338ed15d3ec549ce03b/README.md) reports English IF-Eval (Prompt Strict): GPT-4o0513 84.3 and Claude-3.5-Sonnet-1022 86.5. DeepSeek is the reporting organization. Its note specifies an8K output cap and repeated sampling with varying temperatures for benchmarks under1000 samples. Exact evaluation dates, dataset/scorer revisions and temperatures are not provided in the inspected table; nulls are retained. The source commit date is not the evaluation date.

Local Pro used output2048 and one retained response per prompt, combining78 cache and463 new. These values are not head-to-head measurements, statistical rankings, current-frontier parity or general-intelligence comparisons.

[Qwen3 Technical Report v1](https://arxiv.org/html/2505.09388v1), Table12, also explicitly reports strict prompt and GPT-4o-2024-11-20 at86.5; it is a different snapshot and not substituted for GPT-4o0513. Only the two DeepSeek-reported rows are graphed for consistent source attribution.

Current catalogs were read on2026-09-27: [OpenAI](https://developers.openai.com/api/docs/models/all) lists GPT-6 Astra/Sol/Luna; [Anthropic](https://platform.claude.com/docs/en/models/overview) lists Claude Fable5.1/Opus5.5/Sonnet5. Comparable IFEval strict-prompt results were not verified in the inspected official sources, so they are excluded, not represented as zero. This bounded search does not prove no result exists anywhere.

Machine-readable rows, metric names, source revisions, conditions and unknowns are in `results/external_references.json`. Source-to-bar consistency is tested. No outside evaluation API was used.
