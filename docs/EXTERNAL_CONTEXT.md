# Historical context, not matched performance

Selection includes historical, nearby and higher references; it is not restricted to models below Local Pro. All charted values are English IFEval strict prompt-level accuracy.

The [original IFEval paper, Table 3](https://arxiv.org/pdf/2311.07911) reports GPT-4 at 76.89. The authors (Google/Yale), not OpenAI, report responses obtained in November 2023. The exact API snapshot is not specified and is not inferred. The paper is dated November 15, 2023; source date and response collection period are distinct. Exact generation cap, sampling settings and code/data revisions for that result remain unverified here.

The [Qwen3 Technical Report v1, Table 14](https://arxiv.org/html/2505.09388v1#S4.T14), published May 14, 2025 by the Qwen Team, explicitly labels GPT-4o-mini-2024-07-18 at 80.4 as IFEval strict prompt. Its evaluation date and GPT-specific generation settings are not established here; Qwen generation settings are not attributed to the GPT baseline. This near reference is above Local Pro's 79.67, not a Local Pro win.

The [pinned DeepSeek-V3 README](https://github.com/deepseek-ai/DeepSeek-V3/blob/9b4e9788e4a3a731f7567338ed15d3ec549ce03b/README.md) reports English IF-Eval (Prompt Strict): GPT-4o0513 84.3 and Claude-3.5-Sonnet-1022 86.5. DeepSeek is the reporting organization. Its note specifies an8K output cap and repeated sampling with varying temperatures for benchmarks under1000 samples. Exact evaluation dates, dataset/scorer revisions and temperatures are not provided in the inspected table; nulls are retained. The source commit date is not the evaluation date.

Local Pro used output2048 and one retained response per prompt, combining78 cache and463 new. These values are not head-to-head measurements, statistical rankings, current-frontier parity or general-intelligence comparisons.

[Qwen3 Technical Report v1](https://arxiv.org/html/2505.09388v1), Table12, also reports GPT-4o-2024-11-20 at86.5; it is a different snapshot and not substituted for GPT-4o0513. The chart now includes four external references from three sources, with per-row attribution. Lower Claude results whose exact strict/loose metric is ambiguous are excluded.

Current catalogs were read on2026-09-27: [OpenAI](https://developers.openai.com/api/docs/models/all) lists GPT-6 Astra/Sol/Luna; [Anthropic](https://platform.claude.com/docs/en/models/overview) lists Claude Fable5.1/Opus5.5/Sonnet5. Comparable IFEval strict-prompt results were not verified in the inspected official sources, so they are excluded, not represented as zero. This bounded search does not prove no result exists anywhere.

Machine-readable rows, metric names, source revisions, conditions and unknowns are in `results/external_references.json`. Source-to-bar consistency is tested. No outside evaluation API was used.
