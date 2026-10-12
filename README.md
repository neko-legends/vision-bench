# vision-bench

Can a cheap vision model replace an expensive one for **image QC / frame judging**?

This repo is a small, reproducible bake-off: 12 film stills, judged by a spread of vision models on
Venice, scored against a baseline. It exists because "which vision model is good" is usually answered
with vibes — and because the interesting finding turned out to be about **latency and timeouts**, not
raw model quality.

## The data (and why it's safe to publish)

The 12 images are **generated film stills** from a personal short-film project (Sadie) — no private
photos, no personal documents. They come from three image generators × two styles × two subjects:

- generators: `gpt-image-2-5-sunburst`, `nano-banana-2-1`, `flux-3-image`
- styles: `stopmotion` (Laika-style), `anime` (Makoto-Shinkai-style)
- subjects: `sheet` (character turnaround), `crawl` (a scene: ghost girl crawling out of a CRT TV)

Each image ships with the exact prompt that generated it (`prompts.json`) and the baseline verdict
(`<image>.astra.txt`).

## Method

Per image, two calls:

1. **Judge call** — the strict QC prompt (STYLE score/10, CONTENT score/10, DEFECTS, one-line verdict),
   `max_tokens=400`, `temperature=0`.
2. **Known-answer call** — "Answer with exactly one word, yes or no: is the ghost girl's face visible
   through the hair?" — a cheap correctness probe with a ground truth.

Raw per-call records (model, image, latency, tokens, cost, response) are in `results/*.jsonl`.
The full write-up is `results/vision-bakeoff.md`.

## Results

See `results/vision-bakeoff.md` and `charts/vision-scoreboard.jpg`.

**Headline finding:** the model that "kept failing" in production was the *cheapest* one — fastest on
small images, but **47 s on a large image** against a 60 s timeout, with no fallback. A model costing
~2× more per token finished the same large image in **18 s** and never failed. Per-token price is not
per-task cost; wall-clock against your real input size is what decides reliability.

## ⚠️ Caveat: the baseline is self-graded

The baseline verdicts were produced by **Astra**, which is also one of the models in the comparison.
So Astra is grading a field that includes itself. Treat the baseline as "the incumbent's opinion", not
neutral ground truth. A neutral re-judge is a known follow-up.

## Reproduce

```bash
# any OpenAI-compatible vision endpoint; here: Venice
export VENICE_API_KEY=...
python3 run.py --model <model-id> --out results/<model-id>.jsonl
```

`run.py` reads `frames/**`, applies the two prompts, and appends one JSON row per call with latency,
token counts and cost. Models run in parallel; images are sequential per model.

**Rate limits:** Venice returns `429` if you push concurrency. `--workers 1` is safe; `2` usually is
too. A `429` is recorded as an `error` row, not a crash — re-run to fill gaps.

## Models tested

Cheap tier: `qwen-3-8-flash`, `qwen-3-8-27b`, `z-ai-glm-5-3-flash`, `deepseek-v4-1-flash`,
`xiaomi-mimo-v2-6-flash`, `luna`. Expensive tier: `claude-sonnet-5-5`, `openai-gpt-61-sol`.
Privacy tags (`private` / `anonymized`) are recorded per model — a private model is required if the
images ever contain personal data.

## License

Frames and results: MIT. The film stills are from the Sadie project.
