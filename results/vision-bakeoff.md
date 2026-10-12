# Vision bake-off: can a cheap Venice model replace Astra for frame judging?

Date: 2026-10-11 · non-personal data (film style-test frames) · working dir `films/sadie/storyboard/style-tests/`

**Question.** Astra (the current judge) grades these Sadie style-test frames. Can a cheaper Venice vision
model do the frame QC instead?

**Setup.** 12 images (3 generators × {stop-motion, anime} × {character sheet, crawl scene}) judged by 4
Venice vision models, plus five further arms added on 2026-10-11 (below), using the *exact* Astra prompts (`max_tokens=400`, `temperature=0`), plus a second
yes/no known-answer call per image: *"is the ghost girl's face visible?"*. Baseline = Astra's
`<image>.astra.txt` verdicts. Raw per-call data: `vision-bakeoff.jsonl` (217 rows = 216 successful calls
plus the one recorded failure row, which carries no `cost_usd`; see the added-arm entries below).

**Added 2026-10-11: a fifth arm, `z-ai-glm-5-3-flash`.** Same 12 images, same two prompt strings (copied
verbatim from the stored records), `max_tokens=400`, `temperature=0`, 120 s timeout, images sequential.
It is reasoning-capable (`supportsReasoning: true`, `supportsReasoningEffort: false`, vision `true`,
privacy tag `private` in `GET /api/v1/models?type=text`), so it got the same thinking-off handling as
`qwen-3-8-flash`: `venice_parameters.disable_thinking=true`. Measured effect of that switch on one frame:
with thinking on it emitted 111 hidden reasoning tokens and judged STYLE 5/10; with thinking off, 0
reasoning tokens and a complete 5-line answer (STYLE 9/10) — so thinking-off is also what keeps the fixed
400-token budget for the answer. The first pass of this arm was run with all 24 calls concurrent (a
mistake: it inflates latency to a 24 s median by queueing); that run was discarded and the arm re-run
images-sequential to match the other four arms' latency basis. Cost of the discarded pass is excluded from
the table below. Only the four original models' rows were left untouched.

**Added 2026-10-11: a sixth arm, `qwen-3-8-27b`.** Same 12 images, same two prompt strings (copied verbatim
from the stored records), `max_tokens=400`, `temperature=0`, 120 s timeout, images sequential within the
model — the original runner unchanged except for the model id, the pricing and the thinking switch, run into
its own raw file (`vision-bakeoff-qwen38-27b.jsonl`). Catalogue check
(`GET /api/v1/models?type=text`): present with `supportsVision: true`, privacy tag `private`,
`"uncensored": true` — the only arm of the six whose live metadata carries an uncensored flag
(`z-ai-glm-5-3-flash` does not) — `betaModel: true`, $0.45/M input and $3.20/M output with **no catalogue
cache rate**, so its one cached-token call is billed at the input rate here (conservative, it can only
overstate the cost). It exposes `reasoningEffort` options including `none` (default `xhigh`), so it got the
deepseek/xiaomi-style switch (`reasoning_effort=none`): 0 reasoning tokens on all 24 calls, `finish_reason:
stop` everywhere. Raw rows: 25 records — 24 successful calls plus one `ConnectionResetError` row on the
`flux/sheet-anime` judge call, whose retry supplies the scored answer and is the last record for that cell
(so last-wins readers get the answer; the failure row is self-describing, it has an `error` key and no
`response`). Verdict: **it does not change the pick** — it ties `z-ai-glm-5-3-flash` on score MAD (mean
0.64) and is the second-lowest hallucinator of the six (2 spurious claims vs `qwen-3-8-flash`'s 6), but it
is worse than the incumbent on exactly what this job needs: face-visible agreement 8/11 with three false
positives (vs 11/11) and Astra-named defect recall 6/25 (vs 12/25), at 6.7× the incumbent's run cost
($0.0651 vs $0.0097).

**Added 2026-10-11: an eighth arm, `openai-gpt-6-luna`.** Same 12 images, same two prompt strings (copied
verbatim from the stored records), `max_tokens=400`, `temperature=0`, 120 s timeout, images sequential
within the model, run into its own raw file (`vision-bakeoff-luna.jsonl`). Catalogue check
(`GET /api/v1/models?type=text`): present with `supportsVision: true`, privacy tag `anonymized` (the third
`anonymized` arm after `qwen-3-8-flash` and `claude-sonnet-5-5`), and **no** `uncensored` flag anywhere in
its live metadata — checked, not inferred: the same response carries `"uncensored": true` on 13 other
models and `openai-gpt-6-luna`'s `model_spec` has no such key (its `traits` list is empty). It reports
`supportsReasoning: true`, `supportsReasoningEffort: true`, `reasoningEffortOptions`
none/low/medium/high/xhigh/max (`defaultReasoningEffort: high`), $0.125/M input, $0.0125/M cached input,
$0.15625/M cache write and $0.625/M output.

Thinking handling: `reasoning_effort=none`, the switch the other `supportsReasoningEffort` arms
(deepseek, xiaomi, qwen-3-8-27b) got. Measured on the `flux/crawl-anime` judge prompt (identical body
except the parameter): at the default (effort `high`) it burned 255 of 344 output tokens on hidden
reasoning (`reasoning_tokens: 255`) and returned a compressed 3-line answer; with `reasoning_effort=none`
it emitted 0 reasoning tokens and the complete 5-line answer. `venice_parameters.disable_thinking=true`
also works on this model (measured: 123 output tokens, no reasoning) but was not used, so this arm's switch
matches the other effort-capable arms. All 24 recorded calls came back `finish_reason: stop`, 0 errors,
0 truncated answers, `reasoning_chars: 0`.

Cost-accounting deviation: this is the only arm whose live rate card has a distinct **cache-write** rate and
whose calls create cache entries (up to 5 104 tokens per call). Its `cost_usd` therefore prices
cache-creation tokens at the catalogue cache-write rate rather than at the input rate the other arms'
three-term formula implies, and its rows carry an extra `cache_write_tokens` key:
`cost = fresh×0.125 + cache_read×0.0125 + cache_write×0.15625 + out×0.625` (per 1M tokens). Recomputing it
the other arms' way (cache-write charged as input) would report $0.0145 instead of the recorded $0.0186
(+$0.0041); the recorded figure is the higher, actual one. Everything else is the protocol above (same
runner as the `z-ai-glm-5-3-flash` arm, model id and pricing changed).

Raw rows: 24 records, 0 errors, kept in their own file `vision-bakeoff-luna.jsonl` and appended to
`vision-bakeoff.jsonl`. Verdict: **it does not change the pick** — see §4.

**Added 2026-10-11: a seventh arm, `claude-sonnet-5-5`.** Same 12 images, same two prompt strings (copied
verbatim from the stored records), `max_tokens=400`, `temperature=0`, 120 s timeout, images sequential
within the model. Catalogue check (`GET /api/v1/models?type=text`): present with `supportsVision: true`,
privacy tag `anonymized` (the second `anonymized` arm after the incumbent), and **no** `uncensored` flag in
its live metadata — checked, not inferred: the same response carries `"uncensored": true` on 12 other
models (including `qwen-3-8-27b`), and `claude-sonnet-5-5`'s `model_spec` has no such key (its `traits`
list is empty). It reports `supportsReasoning: true`, `reasoningEffortOptions`
low/medium/high/xhigh/max (**no `none`**), `defaultReasoningEffort: medium`, $2.50/M input, $0.125/M
cached input and $12.50/M output.

Thinking handling: `venice_parameters.disable_thinking=true`, the same switch the `qwen-3-8-flash` and
`z-ai-glm-5-3-flash` arms used. Measured on the `sunburst/sheet-anime` judge prompt (identical body
except the switch): the default (thinking on, effort `medium`) burned **all 400 tokens on hidden reasoning
and returned empty content** with `finish_reason: length` and a populated `reasoning_details`; with
`disable_thinking=true` the same prompt returned a complete 926-char answer and `finish_reason: stop`.
`reasoning_effort: none` also works on this model (the endpoint accepts it although the catalogue does not
list it) and produced the same thinking-off behaviour (885-char answer, no `reasoning_details`);
`reasoning_effort: xhigh` reproduced the empty/`length` failure. All 24 recorded calls came back with
`reasoning_chars: 0`, i.e. no hidden scratchpad was billed inside the answer budget.

Two disclosed deviations from the other arms. (a) **Image encoding:** four of the twelve source PNGs
base64-encode above Venice's 10 MB image cap **for this model only** — `sunburst/crawl-stopmotion`,
`nano/crawl-anime`, `nano/crawl-stopmotion`, `nano/sheet-stopmotion`; the endpoint rejects them with
`image exceeds 10 MB maximum: 13757936 bytes > 10485760 bytes` (10 485 760 base64 chars). Those four were
sent as JPEG q98 4:4:4 re-encodes at **identical pixel dimensions** (PSNR 46.7-48.2 dB against the PNG, so
visually lossless for judging), recorded per row in an `image_encoding` key; the other eight images were
sent verbatim. The limit is on the base64 payload, not the file, so `sunburst/crawl-anime` (7.66 MB file →
10 214 292 chars) still passed and was sent as the original PNG. Verified by direct probe: all four
over-cap PNGs are rejected (10 757 912 / 13 757 936 / 14 515 644 / 10 980 104 base64 chars, each
`400 image exceeds 10 MB maximum`) and all four under-cap PNGs are accepted. (b) **Truncation:** two of its 24 answers
hit the 400-token ceiling with `finish_reason: length` — the `flux/crawl-stopmotion` and
`nano/crawl-stopmotion` judge calls; the second one's verdict line is cut mid-sentence (`"...Strong
stylistic hit with mostly"`), but its STYLE/CONTENT/DEFECTS lines are complete, so scoring is unaffected.
Raw rows: 24 records, 0 errors, kept in their own file `vision-bakeoff-sonnet55.jsonl` and appended to
`vision-bakeoff.jsonl`. Verdict: **it does not change the pick** — see §4.

**Added 2026-10-11: a ninth arm, `openai-gpt-61-sol`.** Same 12 images, same two prompt strings (copied
verbatim from the stored records), `max_tokens=400`, `temperature=0`, 120 s timeout, images sequential
within the model, run into its own raw file (`vision-bakeoff-sol61.jsonl`) and appended to
`vision-bakeoff.jsonl`. Catalogue check (`GET /api/v1/models?type=text`): present with `supportsVision:
true`, privacy tag `anonymized` (the fourth `anonymized` arm of the nine), and **no `uncensored` label
anywhere in its live metadata** — checked, not inferred: its `model_spec` has no `uncensored` key and an
empty `traits` list, while the same response carries `"uncensored": true` on 13 other models (including
`qwen-3-8-27b`). It reports `supportsReasoning: true`, `reasoningEffortOptions`
low/medium/high/xhigh/max (**no `none`**), `defaultReasoningEffort: high`, 1.05 M context, $2.50/M input,
$0.125/M cached input, **$3.125/M cache write** and $12.50/M output (extended rates only above 272 k
context, far above this run's ≈6.7 k).

Thinking handling: this is the arm where the two switches diverge, so both were measured on one frame
(`flux/sheet-stopmotion`, identical body otherwise). `venice_parameters.disable_thinking=true` — the
switch `qwen-3-8-flash`, `z-ai-glm-5-3-flash` and `claude-sonnet-5-5` used — is **ineffective on this
model**: it still emitted **170-269 hidden reasoning tokens** (`completion_tokens_details.reasoning_tokens`,
259-365 completion tokens against 87-123 when thinking was actually off) and took 8-11 s instead of ~4.3 s.
`reasoning_effort=none` is accepted by the endpoint even though the catalogue does not list it, and measured
0 reasoning tokens; so did the **lowest documented effort, `reasoning_effort=low`**. Because `none` is
undocumented for this model the arm uses `reasoning_effort=low`: all 24 recorded calls came back with no
`reasoning_chars`, no `finish_reason: length` and no truncation, and 23 of 24 reported no
`reasoning_tokens` at all (the exception is the `sunburst/sheet-anime` face probe, which spent 18 reasoning
tokens inside a 25-token completion and still answered a clean one-word `no`). Raw rows: 24 records, 0
errors, 0 retries (the runner allows 3 attempts per call). The arm needed **no image re-encoding**: the
10 MB base64 cap that forced JPEG re-encodes for `claude-sonnet-5-5` did not fire here — the two >10 MB
source PNGs (`nano/crawl-anime`, `nano/crawl-stopmotion`) were sent verbatim and accepted.

Cost accounting: like `openai-gpt-6-luna`, this arm's rate card has a distinct **cache-write** rate and all
24 calls create cache entries, so its rows are priced on the four-term basis —
`fresh×2.50 + cache_read×0.125 + cache_write×3.125 + out×12.50` (per 1M) — which reproduces Venice's own
`cost.diem` to the cent ($0.352991 recorded vs $0.3529905 reported) and gives the table's $0.3530. The
earlier arms' three-term formula (cache writes charged as plain input) would report $0.2870; that figure is
kept per row in a `cost_usd_3term` key. `claude-sonnet-5-5` has the same two rates but is recorded on the
three-term basis, so its $0.3628 is likewise a slight understatement. Rows also carry `cache_write_tokens`
and `diem`.

Raw rows: 24 records, kept in their own file `vision-bakeoff-sol61.jsonl` and appended to
`vision-bakeoff.jsonl`. Verdict: **it does not change the pick** — see §4.

**Method notes (constant across models).** Source images as `image_url` data URIs (full resolution; see the
`claude-sonnet-5-5` entry for the four frames that had to be re-encoded for that model's 10 MB cap;
the `openai-gpt-61-sol` arm needed no re-encode, so its 24 calls used the source files verbatim);
identical prompt text; `max_tokens=400`; `temperature=0`; 120 s timeout; models run in parallel, images
sequential within a model. Hidden reasoning was disabled on every reasoning-capable arm (all nine)
(`reasoning_effort=none` for deepseek, xiaomi, qwen-3-8-27b and openai-gpt-6-luna; `venice_parameters.disable_thinking=true`
for qwen-3-8-flash, z-ai-glm-5-3-flash and claude-sonnet-5-5; `reasoning_effort=low`, the documented floor
for a model with no `none` option, for openai-gpt-61-sol — its entry explains why the disable_thinking
switch was rejected there) so the fixed 400-token budget is spent on
the answer, not on a
scratchpad. Without this
deepseek/xiaomi/qwen-3-8-flash/sonnet-5-5 returned truncated or empty answers and the run would have
measured token
budgeting rather than judging. This is a deliberate deviation from a naive reading of the brief and is
disclosed here. All nine target models were confirmed present with `supportsVision: true` in
`GET https://api.venice.ai/api/v1/models?type=text` (including `xiaomi-mimo-v2-6-flash`, so none was
skipped; the five added arms were checked against that same live response). Pricing for the cost column was read live from that same response.

## Cost & latency

| model | calls | ok | median latency (s) | max latency (s) | in-tok | out-tok | cost (usd) | privacy (catalogue) |
|---|---|---|---|---|---|---|---|---|
| `deepseek-v4-1-flash` | 24 | 24 | 2.45 | 3.42 | 42426 | 1834 | 0.0127 | private |
| `qwen3-vl-235b-a22b` | 24 | 24 | 4.10 | 16.34 | 136866 | 912 | 0.0305 | private |
| `xiaomi-mimo-v2-6-flash` | 24 | 24 | 6.21 | 21.61 | 136770 | 1785 | 0.0177 | private |
| `qwen-3-8-flash` | 24 | 24 | 4.68 | 9.07 | 104298 | 1379 | 0.0097 | anonymized |
| `z-ai-glm-5-3-flash` (added 2026-10-11) | 24 | 24 | 2.72 | 5.61 | 166628 | 1643 | 0.0256 | private |
| `qwen-3-8-27b` (added 2026-10-11) | 24 | 24 | 3.98 | 31.30 | 138618 | 858 | 0.0651 | private |
| `claude-sonnet-5-5` (added 2026-10-11) | 24 | 24 | 4.65 | 6.89 | 182634 | 4299 | 0.3628 | anonymized |
| `openai-gpt-6-luna` (added 2026-10-11) | 24 | 24 | 5.48 | 7.13 | 155784 | 1199 | 0.0186 | anonymized |
| `openai-gpt-61-sol` (added 2026-10-11) | 24 | 24 | 5.97 | 11.89 | 155976 | 1317 | 0.3530 | anonymized |
| **total** | 217 | 216 | | | 1220000 | 15226 | **0.8957** | |

`privacy` is the model's tag in the same live catalogue response. It is irrelevant to this corpus (film
style-test frames, no personal data) but decides whether an arm can ever grade private frames —
`qwen-3-8-flash` is one of four `anonymized` arms of the nine (the others are
`claude-sonnet-5-5`, `openai-gpt-6-luna` and `openai-gpt-61-sol`); the five others are `private`.

Errors/timeouts: **0/120** successful calls in the recorded data of the original four arms and
`z-ai-glm-5-3-flash`; the `qwen-3-8-27b` arm records one failure row (25 records for 24 calls) — a
transient `Connection reset by peer` on the `flux/sheet-anime` judge call, retried successfully and kept in
the raw file. The added arm hit two transient `Connection reset by peer`
HTTP failures during its discarded concurrent pass; both were retried and no failed call is recorded.
The `claude-sonnet-5-5` arm records 0 errors and 0 timeouts in its 24 rows, but 2 of its 24 answers were
**truncated at the 400-token ceiling** (`finish_reason: length`, no HTTP error): the
`flux/crawl-stopmotion` and `nano/crawl-stopmotion` judge calls (see its setup entry).
Cost cap was $1.00 for the original four arms ($0.0705 spent) and $0.50 for the added arm ($0.0256 recorded;
≈ $0.026 for the discarded concurrent pass and ≈ $0.005 of probes, so ≈ $0.057 total for this arm). One
added-arm call (`nano/sheet-stopmotion` face probe) hit 1 536 cached input tokens, priced at the catalogue
cache rate ($0.03/M) rather than $0.15/M. The `claude-sonnet-5-5` arm ran under a $1.00 cap and recorded
$0.3628 across its 24 calls (it sends the most image tokens of the seven: 182.6 k in, of which 62.1 k were
cache reads, at $2.50/M input and $12.50/M output); its four abandoned probe calls cost nothing (HTTP 400),
its eight exploratory probe calls cost ≈ $0.151, the four accepted calls of the 10 MB-cap check below cost
≈ $0.050 and the eight determinism repeats ≈ $0.100, so ≈ **$0.663** total for that arm — inside the cap
(the 20 extra calls are not in `vision-bakeoff.jsonl`, whose sonnet55 rows are exactly the 24 scored ones).
The `openai-gpt-6-luna` arm records 0 errors, 0 timeouts and 0 truncated answers in its 24 rows; it ran
under the brief's $1.00 cap and recorded $0.0186 (plus ≈$0.002 of parameter probes, ≈$0.021 total for
this arm, inside the cap).
The `openai-gpt-61-sol` arm ran under a $1.00 cap and records **0 errors, 0 retries and 0 truncations** in
its 24 rows; its ≈14 exploratory probe calls cost ≈ $0.13, so ≈ **$0.49** total for the arm, inside the
cap. Its $0.3530 is the four-term (cache-write-inclusive) figure — the highest-fidelity number in the
column, since it equals Venice's `cost.diem` to the cent; the three-term basis every earlier arm's row uses
would give $0.2870 for the same calls. That makes the column a mix of bases rather than one formula: only
`openai-gpt-6-luna` and `openai-gpt-61-sol` price their cache writes, so both are stated at their actual
(higher) spend, while `claude-sonnet-5-5` — which has the identical cache-write rate — is stated slightly
below its actual spend. Read this column as "recorded basis, higher is more accurate where a cache-write
rate existed" rather than as one apples-to-apples formula.

## 1. Face-visible agreement with Astra

Astra flagged the face as visible on **7 of 12** images (read from the `.astra.txt` files, not taken on trust):
flux crawl-anime, flux crawl-stopmotion, flux sheet-stopmotion, sunburst sheet-stopmotion,
nano crawl-stopmotion, nano sheet-anime, nano sheet-stopmotion. Four images were not flagged
(sunburst crawl-anime, sunburst crawl-stopmotion, sunburst sheet-anime, nano crawl-anime). One baseline is
**indeterminate**: `flux-3-image/sheet-anime`'s Astra file is truncated after `STYLE 7/10 - painterly` and
says nothing about the face, so it is excluded from the agreement score (11 determinate images).

| model | face agreement | yes-rate | Astra=visible but model=no | Astra clean but model=yes |
|---|---|---|---|---|
| `deepseek-v4-1-flash` | **8/11** | 8/12 | flux/crawl-anime | sunburst/crawl-anime, sunburst/crawl-stopmotion |
| `qwen3-vl-235b-a22b` | **10/11** | 6/12 | flux/crawl-anime | none |
| `xiaomi-mimo-v2-6-flash` | **10/11** | 8/12 | none | nano/crawl-anime |
| `qwen-3-8-flash` | **11/11** | 7/12 | none | none |
| `z-ai-glm-5-3-flash` (added 2026-10-11) | 9/11 | 9/12 | none | sunburst/crawl-stopmotion, nano/crawl-anime |
| `qwen-3-8-27b` (added 2026-10-11) | **8/11** | 10/12 | none | sunburst/crawl-anime, sunburst/crawl-stopmotion, nano/crawl-anime |
| `claude-sonnet-5-5` (added 2026-10-11) | **8/11** | 10/12 | none | sunburst/crawl-anime, sunburst/crawl-stopmotion, nano/crawl-anime |
| `openai-gpt-6-luna` (added 2026-10-11) | **8/11** | 10/12 | none | sunburst/crawl-stopmotion, sunburst/sheet-anime, nano/crawl-anime |
| `openai-gpt-61-sol` (added 2026-10-11) | **8/11** | 10/12 | none | sunburst/crawl-anime, sunburst/crawl-stopmotion, nano/crawl-anime |

`yes-rate` counts yes answers on the 11 determinate images (the indeterminate flux/sheet-anime call is
excluded from the numerator) — the convention the original four rows were computed with, so the column sums
against `face agreement`, not against the 12 face calls made.

Per-image matrix (`OK` = agrees with Astra; `x` = disagrees; `?` = indeterminate baseline):

| image | Astra | deepseek | qwen3 | xiaomi | qwen | glm53 | qwen27b | sonnet55 | luna | sol61 |
|---|---|---|---|---|---|---|---|---|---|---|
| flux/crawl-anime | visible | X/no | X/no | OK/yes | OK/yes | OK/yes | OK/yes | OK/yes | OK/yes | OK/yes |
| flux/crawl-stopmotion | visible | OK/yes | OK/yes | OK/yes | OK/yes | OK/yes | OK/yes | OK/yes | OK/yes | OK/yes |
| flux/sheet-anime | ? | ?/yes | ?/yes | ?/yes | ?/yes | ?/yes | ?/yes | ?/yes | ?/yes | ?/yes |
| flux/sheet-stopmotion | visible | OK/yes | OK/yes | OK/yes | OK/yes | OK/yes | OK/yes | OK/yes | OK/yes | OK/yes |
| sunburst/crawl-anime | clean | X/yes | OK/no | OK/no | OK/no | OK/no | X/yes | X/yes | OK/no | X/yes |
| sunburst/crawl-stopmotion | clean | X/yes | OK/no | OK/no | OK/no | X/yes | X/yes | X/yes | X/yes | X/yes |
| sunburst/sheet-anime | clean | OK/no | OK/no | OK/no | OK/no | OK/no | OK/no | OK/no | X/yes | OK/no |
| sunburst/sheet-stopmotion | visible | OK/yes | OK/yes | OK/yes | OK/yes | OK/yes | OK/yes | OK/yes | OK/yes | OK/yes |
| nano/crawl-anime | clean | OK/no | OK/no | X/yes | OK/no | X/yes | X/yes | X/yes | X/yes | X/yes |
| nano/crawl-stopmotion | visible | OK/yes | OK/yes | OK/yes | OK/yes | OK/yes | OK/yes | OK/yes | OK/yes | OK/yes |
| nano/sheet-anime | visible | OK/yes | OK/yes | OK/yes | OK/yes | OK/yes | OK/yes | OK/yes | OK/yes | OK/yes |
| nano/sheet-stopmotion | visible | OK/yes | OK/yes | OK/yes | OK/yes | OK/yes | OK/yes | OK/yes | OK/yes | OK/yes |

`glm53` = `z-ai-glm-5-3-flash`, `qwen27b` = `qwen-3-8-27b`, `sonnet55` = `claude-sonnet-5-5`,
`luna` = `openai-gpt-6-luna` and `sol61` = `openai-gpt-61-sol` (all added 2026-10-11; the same
abbreviations are used in the score and defect tables below). `sonnet55`'s three false positives are exactly
`qwen27b`'s three — `sunburst/crawl-anime`, `sunburst/crawl-stopmotion` and `nano/crawl-anime`, i.e. the
frames Astra called face-covered that models keep re-flagging — and `sol61` lands on **the same three
cells**, so those three arms sit at 8/11 through identical cells and they are the only three that answer
`yes` to all three of those frames. `luna` shares two of `qwen27b`'s three false positives
(`sunburst/crawl-stopmotion`, `nano/crawl-anime`) but trades the third for `sunburst/sheet-anime` — the only
sheet it calls face-exposed where Astra reads the face as covered — while `deepseek-v4-1-flash` also ends at
8/11 through a different mix. So 8/11 is the worst figure in the column, reached by five of the nine arms,
and the incumbent's 11/11 remains unique. `sol61` is the second arm (after `sonnet55`) whose *judge* line is
the better instrument on this question: read off its judge text it flags the exposed face on all 7 frames
Astra flagged (FACE 7/7, §3), while its isolated probe is the one producing the three false positives.

## 2. Score agreement with Astra

Mean absolute difference vs Astra's own scores (lower = closer). STYLE is scored on all 12; the second
score is CONTENT on the 6 crawl images and CONSISTENCY on the 6 sheets.

| model | STYLE MAD | CONTENT/CONSISTENCY MAD | mean of both |
|---|---|---|---|
| `deepseek-v4-1-flash` | 1.00 | 1.18 | 1.09 |
| `qwen3-vl-235b-a22b` | 1.33 | 1.55 | 1.44 |
| `xiaomi-mimo-v2-6-flash` | 0.92 | 1.00 | 0.96 |
| `qwen-3-8-flash` | 0.67 | 0.55 | 0.61 |
| `z-ai-glm-5-3-flash` (added 2026-10-11) | 0.83 | 0.45 | 0.64 |
| `qwen-3-8-27b` (added 2026-10-11) | 0.83 | 0.45 | 0.64 |
| `claude-sonnet-5-5` (added 2026-10-11) | 0.58 | 0.77 | 0.68 |
| `openai-gpt-6-luna` (added 2026-10-11) | 0.67 | 0.64 | 0.66 |
| `openai-gpt-61-sol` (added 2026-10-11) | **0.33** | **0.27** | **0.30** |

Per-image scores (Astra vs each model; `C`=CONTENT, `Cons`=CONSISTENCY):

| image | Astra | deepseek | qwen3 | xiaomi | qwen | glm53 | qwen27b | sonnet55 | luna | sol61 |
|---|---|---|---|---|---|---|---|---|---|---|
| flux/crawl-anime | S9/C7 | S7/C8 | S9/C8 | S9/C8 | S9/C8 | S9/C8 | S9/C7 | S9/C7 | S9/C8 | S9/C7 |
| flux/crawl-stopmotion | S8/C7 | S7/C6 | S9/C8 | S9/C9 | S8/C7 | S9/C8 | S7/C8 | S8/C6 | S6/C7 | S8/C7 |
| flux/sheet-anime | S7/Cons? | S7/Cons8 | S9/Cons10 | S8/Cons6 | S8/Cons9 | S8/Cons7 | S8/Cons9 | S8/Cons8 | S8/Cons7 | S8/Cons8 |
| flux/sheet-stopmotion | S8/Cons9 | S8/Cons7 | S9/Cons10 | S8/Cons7 | S9/Cons8 | S9/Cons8 | S9/Cons9 | S8/Cons8 | S8/Cons7 | S8/Cons8 |
| sunburst/crawl-anime | S9/C9 | S7/C8 | S9/C8 | S9/C10 | S8/C9 | S9/C9 | S9/C8 | S8/C8 | S9/C7 | S9/C9 |
| sunburst/crawl-stopmotion | S8/C9 | S8/C7 | S9/C10 | S9/C10 | S8/C9 | S9/C9 | S8/C9 | S7/C8.5 | S8/C8 | S8/C9 |
| sunburst/sheet-anime | S7/Cons8 | S8/Cons7 | S9/Cons10 | S8/Cons7 | S8/Cons9 | S9/Cons8 | S8/Cons9 | S7/Cons7.5 | S8/Cons8 | S8/Cons8 |
| sunburst/sheet-stopmotion | S7/Cons8 | S9/Cons8 | S9/Cons10 | S9/Cons8 | S9/Cons8 | S6/Cons8 | S9/Cons9 | S8/Cons8.5 | S6/Cons7 | S7/Cons8 |
| nano/crawl-anime | S7/C7 | S4/C5 | S8/C9 | S9/C8 | S7/C6 | S6/C8 | S8/C7 | S6/C8 | S7/C7 | S8/C8 |
| nano/crawl-stopmotion | S8/C8 | S8/C6 | S9/C10 | S9/C9 | S8/C7 | S9/C9 | S9/C8 | S8/C7 | S7/C8 | S8/C7 |
| nano/sheet-anime | S6/Cons8 | S6/Cons8 | S9/Cons10 | S7/Cons8 | S6/Cons9 | S6/Cons8 | S6/Cons8 | S7/Cons6 | S7/Cons8 | S6/Cons8 |
| nano/sheet-stopmotion | S7/Cons8 | S8/Cons7 | S9/Cons10 | S8/Cons7 | S9/Cons8 | S8/Cons8 | S9/Cons9 | S8/Cons8 | S8/Cons8 | S8/Cons8 |

`sonnet55` is scored off its own text with the same `STYLE n/10` / `CONTENT|CONSISTENCY n/10` reading the
other columns use; it emits half-points (8.5, 7.5, 6.5-style precision), which are
kept as-is rather than rounded. Its best cell is `flux/crawl-anime` (exact STYLE and CONTENT match) and its
worst is `nano/sheet-anime` (S7/Cons6 vs Astra S6/Cons8 — it read the taller, slouched middle view as a
consistency failure, which is the one place it is harsher than Astra). `sol61` is scored the same way and
is the **closest scorer of the nine on both halves** (STYLE MAD 0.33, second-score MAD 0.27; the next best
STYLE MAD is `claude-sonnet-5-5`'s 0.58 and the next best second-score MAD is
`z-ai-glm-5-3-flash`/`qwen-3-8-27b`'s 0.45). Its STYLE score is exactly Astra's on 8 of 12 frames, every
miss is +1, and **no scored cell of its 23 is off by more than one point** on either axis — a property it
shares on STYLE with `claude-sonnet-5-5` (the other arms carry two- and three-point misses). Its largest
read is `nano/crawl-anime`, one point high on both axes.

## 3. Defect detection vs Astra

Hand-coded from the judge text (the automated keyword pass was too crude to trust — it mis-scored obvious
hits such as "hair isn't fully obscuring face"). Categories: FACE (face exposure/coverage), LEAP (boy not
over the couch *arm*), FAINT (faint reads as reclining), PROFILE (middle view too profile-like), HAIR
(length/straightness/wetness/texture), DRESS (nightdress not soaked white), HALFINSIDE (ghost not half-in
the screen), HANDS (stiff/ambiguous hands). `flux-3-image/sheet-anime` has no baseline defects (truncated).

Astra-named-defect recall (fraction of Astra's named issues the model also raised):

| model | overall recall | FACE | LEAP | FAINT | PROFILE | HAIR | DRESS | HALFINSIDE | HANDS |
|---|---|---|---|---|---|---|---|---|---|
| `deepseek-v4-1-flash` | 13/25 (52%) | 7/7 | 1/5 | 0/1 | 1/3 | 2/5 | 1/2 | 0/1 | 1/1 |
| `qwen3-vl-235b-a22b` | 0/25 (0%) | 0/7 | 0/5 | 0/1 | 0/3 | 0/5 | 0/2 | 0/1 | 0/1 |
| `xiaomi-mimo-v2-6-flash` | 16/25 (64%) | 6/7 | 2/5 | 1/1 | 2/3 | 4/5 | 0/2 | 1/1 | 0/1 |
| `qwen-3-8-flash` | 12/25 (48%) | 6/7 | 4/5 | 0/1 | 1/3 | 1/5 | 0/2 | 0/1 | 0/1 |
| `z-ai-glm-5-3-flash` (added 2026-10-11) | 11/25 (44%) | 4/7 | 0/5 | 1/1 | 2/3 | 3/5 | 0/2 | 0/1 | 1/1 |
| `qwen-3-8-27b` (added 2026-10-11) | 6/25 (24%) | 1/7 | 2/5 | 1/1 | 0/3 | 2/5 | 0/2 | 0/1 | 0/1 |
| `claude-sonnet-5-5` (added 2026-10-11) | 17/25 (68%) | **7/7** | 3/5 | 0/1 | 1/3 | 3/5 | **2/2** | **1/1** | 0/1 |
| `openai-gpt-6-luna` (added 2026-10-11) | 9/25 (36%) | 4/7 | 1/5 | 0/1 | 1/3 | 2/5 | 0/2 | 1/1 | 0/1 |
| `openai-gpt-61-sol` (added 2026-10-11) | **22/25 (88%)** | **7/7** | **5/5** | **1/1** | 1/3 | 4/5 | **2/2** | **1/1** | **1/1** |

Defects the model claimed that Astra did **not** name (possible hallucinations), with cross-model corroboration:

| model | spurious claims (count) | notable |
|---|---|---|
| `deepseek-v4-1-flash` | 8 | claimed an anatomy defect on **every** image Astra called anatomically clean (flux crawl x2, sunburst crawl x2, nano crawl-anime, nano crawl-stopmotion) |
| `qwen3-vl-235b-a22b` | 0 | none — never claims a defect Astra didn't name |
| `xiaomi-mimo-v2-6-flash` | 5 | mostly minor (popcorn bowl, pose drift); armature stands on nano sheet-stopmotion corroborated by 2 other models |
| `qwen-3-8-flash` | 6 | 4 anatomy claims on Astra-clean images; extra arm on nano crawl-anime corroborated by deepseek; armature stands corroborated by 2 others |
| `z-ai-glm-5-3-flash` (added 2026-10-11) | 9 | screen-transition claims Astra never made: "lower body dissolves/melts/merges into the screen" on all 4 crawl frames whose screen junction Astra called clean (flux crawl x2, sunburst crawl x2; 3 of the 4 hedged with "plausibly"); "hair hangs oddly detached from body" (nano crawl-anime); garbled on-screen text on 2 frames Astra called text-clean; plus "visible rig stands" on nano sheet-stopmotion and "middle view head tilt hides face inconsistently vs. front view" on sunburst/sheet-anime (Astra flagged that middle view for being profile-like, not for hiding the face) |
| `qwen-3-8-27b` (added 2026-10-11) | 2 | lowest count of the six: no anatomy or text hallucination at all — one FAINT claim on sunburst/crawl-anime where Astra says the three kids' reactions match, and "girl is red-haired instead of white" on nano/crawl-stopmotion (Astra flagged staging there, not casting) |
| `openai-gpt-6-luna` (added 2026-10-11) | 11 | itemised below. Notable: it is the arm that most often misreads the **half-inside requirement** — on 4 crawl frames where Astra affirms the half-in staging it reports the ghost as `fully out`/`mostly outside the screen` (flux/crawl-stopmotion, sunburst/crawl-anime, sunburst/crawl-stopmotion, nano/crawl-stopmotion), a systematic directional error rather than scattered noise; no text hallucinations, and (under the narrow reading) only 1 anatomy claim on a frame Astra called anatomically clean |
| `claude-sonnet-5-5` (added 2026-10-11) | 23 | by far the highest count of the seven, but it also names 2-4 distinct defects per frame where the earlier six name one or two, so the count is dominated by minor observations; itemised below. Notable: it is the only arm to flag the `nano/crawl-anime` fainting-boy legs/couch overlap, and — like `z-ai-glm-5-3-flash` — it claims **garbled text on `flux/crawl-anime` and `nano/crawl-stopmotion`**, two frames Astra explicitly called text-clean; it also keeps claiming anatomy on Astra-clean frames (sunburst/crawl-anime, nano/crawl-stopmotion) |
| `openai-gpt-61-sol` (added 2026-10-11) | 16 | second-highest count of the nine after `claude-sonnet-5-5`, and like that arm it is inflated by granularity: it names 1-4 distinct claims per frame (38 in total: 22 Astra-named hits + these 16) and writes its own explicit `no extra limbs / no text` negations. Breakdown: **5 anatomy claims** on frames Astra explicitly called anatomically clean (flux crawl x2, sunburst crawl-anime, nano crawl x2 — the same class the earlier arms are penalised for); **4 text/pseudo-text claims** on frames Astra called text-clean (garbled prop lettering on flux/crawl-anime and nano/crawl-stopmotion, "background lettering indistinct" on sunburst/crawl-stopmotion, "background pseudo-text" on nano/crawl-anime) — the most of the nine, above `claude-sonnet-5-5`'s 2, though two of the four are softer than "garbled"; **3 age-spec claims** ("proportions read older than 10" on sunburst/sheet-anime, sunburst/sheet-stopmotion, nano/sheet-anime — a judgement against the brief, not an image defect); and one each of face exposure on an Astra-clean sheet (sunburst/sheet-anime, which its own probe also called clean), "hair strands too wavy" (sunburst/sheet-stopmotion), "wetness overly stylized" (nano/sheet-anime) and "visible support bases" (nano/sheet-stopmotion, the contested rig-stands claim). Excluding the 3 age-spec claims the count is 13. Its flux/sheet-anime claims are excluded (truncated baseline) |

The added arm's `11/25` is hand-coded like the other rows, so it is itemised here to stay auditable. Hits:
FACE 4 — flux/sheet-stopmotion ("face partially visible"), sunburst/sheet-stopmotion ("face partially
visible in front view"), nano/sheet-anime ("face partially visible in front view"), nano/sheet-stopmotion
("face partially visible"); the other three exposure frames Astra flagged (flux crawl-anime, flux
crawl-stopmotion, nano crawl-stopmotion) it instead ticked as present ("wet hair over face ✓", "wet black
hair ✓", "wet hair, dripping water, half inside screen ✓"). LEAP 0 — it wrote "Black boy
leaping over arm ✓" on all four arm-frames and "Black boy fleeing ✓" on the fifth. FAINT 1 — flux
crawl-anime ("sleeping/slumped, not clearly fainting backward"). PROFILE 2 — sunburst/sheet-stopmotion
("no three-quarter view — middle is side profile"), nano/sheet-anime ("middle view head angle ambiguous;
no true three-quarter view"). HAIR 3 — flux/sheet-stopmotion ("hair reads dry/waxy, not wet; back view hair
shorter"), nano/sheet-anime ("hair length … vary between views"), nano/sheet-stopmotion ("hair reads as
yarn/locs, not wet strands"). HANDS 1 — sunburst/crawl-stopmotion ("left hand slightly merges with water").
Misses elsewhere: DRESS x2 and HALFINSIDE x1 were never raised. Two judgement calls are worth ±1 each on
HAIR (sunburst/sheet-anime's "hair parting varies" sits in its CONSISTENCY line, not DEFECTS, so it is not
counted) and on PROFILE (nano/sheet-anime's "head angle ambiguous" is counted though it names a head tilt,
not a profile). One more caveat: the arm is not deterministic at `temperature=0` (see below), and a discarded
same-model pre-run of the same prompts landed in the same band but through different cells: FACE 4–5/7 (it
did flag nano crawl-stopmotion's hair as "dry/dreadlocked, not wet-over-face"), HAIR 3/5, HANDS 0/1 →
about 10–11/25. The overall recall figure is therefore good to roughly ±1 across runs and ±1 more across
hand-coding calls.

The `qwen-3-8-27b` `6/25` is hand-coded the same way and itemised to stay auditable. Hits: FACE 1 —
nano/sheet-anime (*"Hair fails to completely cover face in front view"*); the other six exposure frames it
missed (it wrote `DEFECTS: None` on flux/crawl-anime, flux/crawl-stopmotion, sunburst/sheet-stopmotion,
nano/crawl-stopmotion and nano/sheet-stopmotion, and on flux/sheet-stopmotion named only hair *length*
variation across views). LEAP 2 — nano/crawl-anime (*"Black boy is crawling rather than leaping over the
couch arm"*) and nano/crawl-stopmotion (*"boy leaps from couch not over arm"*); on flux crawl x2 and
sunburst/crawl-anime it wrote that the actions were correct. FAINT 1 — flux/crawl-anime (*"the Asian boy is
asleep rather than fainting backward"*). HAIR 2 — flux/sheet-stopmotion and nano/sheet-stopmotion (hair
length/wetness varies between views). It additionally raised FACE on the truncated-baseline
flux/sheet-anime, which counts neither as a hit nor as spurious. PROFILE 0/3, DRESS 0/2, HALFINSIDE 0/1,
HANDS 0/1 — never raised. Judgement calls worth ±1: nano/crawl-anime's "crawling rather than leaping over
the couch arm" is counted as a LEAP hit (it does name the arm), and nano/sheet-anime's hair/face line is
counted as FACE rather than HAIR, the convention already used for `qwen-3-8-flash` on that frame.

The `claude-sonnet-5-5` `17/25` (68%) is the highest recall of the seven, hand-coded the same way and
itemised to stay auditable. Hits: **FACE 7/7** — it flagged the exposed face on every frame Astra did
("her face is visible and downturned, not hanging over it" on flux/crawl-anime; "ghost's hair doesn't cover
her face" on flux/crawl-stopmotion; "Face is NOT covered by hair" on flux/sheet-stopmotion; "the
three-quarter view exposes ear and cheek" on sunburst/sheet-stopmotion; "one eye and cheek are visible" on
nano/crawl-stopmotion; "Front face is not fully covered (nose and mouth visible)" on nano/sheet-anime; "Face
is not fully covered (front view shows nose and mouth)" on nano/sheet-stopmotion). LEAP 3 — flux/crawl-stopmotion ("leaping over the couch's back/mid-air rather than clearly over the arm"), nano/crawl-anime
("mid-stride more than clearly vaulting the couch arm"), nano/crawl-stopmotion ("on the couch back rather
than clearly vaulting the arm"); it credited the leap as present on flux/crawl-anime and
sunburst/crawl-anime, the two it missed. FAINT 0/1 — it recorded the fainting boy as present on
flux/crawl-anime and never called the pose reclining. PROFILE 1 — sunburst/sheet-anime ("The center view
isn't a true three-quarter: it reads as a near-profile"); it missed the profile complaint on
sunburst/sheet-stopmotion and nano/sheet-anime (on the latter it named a "head-down slouch" instead, which
is a pose, not a profile). HAIR 3 — flux/sheet-stopmotion ("Hair is parted and swept to the sides rather
than hanging as a curtain over the face"), sunburst/sheet-anime ("hair's volume and strand density vary
slightly between views"), nano/sheet-stopmotion ("hair looks dry and yarn-like, with only small droplets
rather than truly wet and clumped strands"); it missed nano/sheet-anime's hair-length drift and
nano/crawl-stopmotion's rope-like hair — on the latter it wrote "long wet black hair" as present, i.e. the
same over-crediting in the bundled prompt that the other arms show. **DRESS 2/2** — flux/sheet-stopmotion
("dress looks damp/dirty rather than truly soaked and clinging") and nano/sheet-stopmotion ("the nightdress
is more dry and dirty than soaked"). **HALFINSIDE 1/1** — nano/crawl-anime ("the ghost is perched on the TV
frame/stand rather than crawling *out* of the glass"). HANDS 0/1 — sunburst/crawl-stopmotion: it wrote "the
ghost's arms are slightly long", which is the nearest miss in that category (a judgement call worth ±1:
counting "arms slightly long" as the HANDS item would make it 18/25 and remove one spurious claim).

Its `23` spurious claims are itemised the same way (distinct defect claims where Astra did not name that
defect on that frame, grouped when they are one observation): flux/crawl-anime 2 (screen-emergence
"no clear half-in/half-out transition" — Astra did not flag HALFINSIDE there; "VHS spine text and some
clutter are garbled" — Astra: no intrusive text); flux/crawl-stopmotion 1 ("ghost's lower body is an
unclear tubular, sleeve-like mass … anatomy/transition awkward"); flux/sheet-stopmotion 3 ("sleeves look
slightly stiff"; "the 'three-quarter' view is closer to a mild turn" — Astra flagged PROFILE on three other
sheets, not this one; "the back view's head looks a touch large"); sunburst/crawl-anime 2 ("leaping boy's
near leg and sock are awkward and the hip/leg connection is slightly ambiguous" — Astra: no anatomical
errors; "the ghost's torso/hips merge into the swirling screen effect" — Astra: no merged bodies);
sunburst/crawl-stopmotion 1 ("the ghost's arms are slightly long"); sunburst/sheet-anime 3 ("a visible ear
and a hint of face" — face exposure, which Astra did not flag on that sheet; "the back view's dress has
patchy, blotchy translucency that doesn't match"; "the hands and feet are slightly stiff and generic");
sunburst/sheet-stopmotion 2 ("the dress reads more ragged and translucent than 'soaked nightdress'"; "no
seam or joint detail to sell the puppet-craft look"); nano/crawl-anime 1 ("the fainting boy's legs and the
couch overlap ambiguously" — Astra named only the ghost/screen intersection); nano/crawl-stopmotion 4
("the ghost's hips and legs merge into the screen with a muddled, flat-looking transition"; "her arm and
torso proportions look slightly stretched"; "the VCR label text is garbled" — Astra: no malformed text;
"the fainting boy's raised knee and blanket blend together awkwardly"); nano/sheet-anime 2 ("its pose is a
head-down slouch unlike the stiff front and back"; "hands are simplified and slightly awkward");
nano/sheet-stopmotion 2 ("the hem sits shorter in the back view"; "the figure looks younger than 10
(toddler proportions)"). `flux/sheet-anime` is excluded from both recall and spurious counting (truncated
baseline), as for the other arms.

The `openai-gpt-6-luna` `9/25` (36%) is hand-coded the same way and itemised to stay auditable. Hits:
FACE 4 — flux/sheet-stopmotion (*"Hair doesn't fully cover the face in front/three-quarter views"*),
sunburst/sheet-stopmotion (*"face is partly visible"*), nano/sheet-anime (*"Face is partly visible in front
and three-quarter views"*), nano/sheet-stopmotion (*"Face is visible despite hair intended to completely
cover it"*); it credited the face as covered on the other three exposure frames Astra flagged
(flux/crawl-anime "wet hair over face", flux/crawl-stopmotion "wet hair", nano/crawl-stopmotion no face
complaint at all). LEAP 1 — flux/crawl-anime (*"Black boy is jumping away, not clearly over the couch
arm"*); on flux/crawl-stopmotion it wrote "scrambling over the couch" (the arm is never named), and on
sunburst/crawl-anime, sunburst/crawl-stopmotion and nano/crawl-stopmotion it ticked the leap/flee as
present. FAINT 0/1 — it called the kids' reactions present on flux/crawl-anime. PROFILE 1 —
sunburst/sheet-anime (*"side view exposes an ear"*); its sunburst/sheet-stopmotion line ("three-quarter view
shows an exposed ear") names the ear but not the profile problem, so it is not counted separately. HAIR 2 —
sunburst/sheet-anime (*"Hair is stringy rather than straight"*) and nano/sheet-stopmotion (*"hair and
hem-drips vary between views"*, the convention `qwen-3-8-27b` got on that frame); flux/sheet-stopmotion,
sunburst/sheet-stopmotion, nano/sheet-anime and nano/crawl-stopmotion were never raised. DRESS 0/2 and
HANDS 0/1 — never raised (on sunburst/crawl-stopmotion, where Astra names stiff hands, it wrote `DEFECTS:
No obvious extra limbs, faces, text, or merged bodies`). Judgement calls worth ±1 each: flux/crawl-stopmotion's
"scrambling over the couch" as a LEAP miss (it names the couch but not the arm); sunburst/sheet-anime's
"side view exposes an ear" as the PROFILE hit; nano/sheet-stopmotion's cross-view hair drift as HAIR (the
`qwen-3-8-27b` convention). It also raised FACE on the truncated-baseline flux/sheet-anime, which counts
neither as a hit nor as spurious.

Its `11` spurious claims are itemised the same way (distinct claims where Astra did not name that defect on
that frame): flux/crawl-anime 1 (*"some awkwardly cropped bodies at the frame edges"* — Astra: no defect);
flux/crawl-stopmotion 2 (*"she's fully out, not half inside"* — Astra's own text affirms the half-in crawl;
*"Ghost's lower body is oddly elongated/translucent"* — Astra: no obvious extra limbs/merged bodies);
flux/sheet-stopmotion 2 (*"hands and facial features vary"*; *"the long sleeves obscure the barefoot
silhouette slightly"*); sunburst/crawl-anime 2 (*"Ghost's emergence from the TV is ambiguous"* / "mostly
outside the screen" — Astra affirms "halfway out of CRT"; *"Races are unclear"* — Astra says the three kids'
reactions match and names no casting issue, the same class `qwen-3-8-27b` was counted for on
nano/crawl-stopmotion); sunburst/crawl-stopmotion 1 (*"ghost's lower body is outside, not half inside"* /
"pose/TV emergence is inconsistent with the brief"); sunburst/sheet-anime 2 (*"age reads older than 10"*;
*"front view is nearly frontal, not three-quarter"*); nano/crawl-stopmotion 1 (*"ghost is mostly outside the
screen"* / "Ghost's emergence reads awkwardly"). Excluded as non-spurious: nano/crawl-anime's "Ghost's
head/neck anatomy is distorted and partly merged with the screen" (Astra itself names the "ambiguous
ghost/screen intersection" there), sunburst/sheet-stopmotion's "three-quarter view shows an exposed ear"
(counted as the FACE hit on that frame), and the style/consistency readings Astra itself named
(sunburst/sheet-stopmotion "photorealistic rather than Laika puppet-like", nano/sheet-anime "painterly
texture is subtle"). Under the narrow reading the earlier rows use in prose (an anatomy/text/merged-bodies
claim Astra explicitly denied) the count is **1–2**, so the headline 11 is granularity-sensitive like the
other arms' counts; the unambiguous part is the direction of the staging error — four crawl frames where
Astra affirms the half-in crawl and this arm says the ghost is fully out.

Two caveats on comparability, stated because the number is high. (1) The count depends on how granular the
model's own defect list is: `claude-sonnet-5-5` names 2-4 distinct defects on nearly every frame
(median 2.5) while the earlier six name one or two in a single clause, so a per-claim count penalises it — under the narrower reading the earlier
rows use in prose ("an anatomy/text/merged-bodies claim Astra explicitly denied"), the count is **7**
(flux/crawl-anime text, flux/crawl-stopmotion anatomy, sunburst/crawl-anime anatomy ×2, nano/crawl-anime
anatomy, nano/crawl-stopmotion anatomy + text), still the highest of the seven but the same order as
`deepseek-v4-1-flash`'s 8. (2) Re-deriving `qwen-3-8-flash`'s row under my broader rule gives ≈13 against
the table's 6, so cross-arm spurious counts are hand-coding-sensitive and should be read as ranks, not
ratios. The one class where it is unambiguous is text: it claims garbled text on 2 frames Astra explicitly
called text-clean.

The `openai-gpt-61-sol` `22/25` (88%) is **the highest recall of the nine**, hand-coded the same way and
itemised here to stay auditable. Hits: **FACE 7/7** — it names the exposure on every frame Astra did
("ghost's face is too exposed" flux/crawl-anime; "ghost's face too exposed" flux/crawl-stopmotion; "Face
largely exposed" flux/sheet-stopmotion; "Nose and mouth exposed" sunburst/sheet-stopmotion; "ghost's face
remains exposed" nano/crawl-stopmotion; "Face visibly exposed" nano/sheet-anime; "Face exposed"
nano/sheet-stopmotion). **LEAP 5/5** — the only arm to catch the couch-arm staging on all five
("fleeing boy jumps above cushions rather than over arm", "jumping on cushions rather than over couch arm",
"vaults the couch back rather than its arm", "half-inside positioning and couch-arm leap are ambiguous",
"jumps across cushions, not over the arm"). FAINT 1/1 — flux/crawl-anime ("fainting boy is already
reclined"). PROFILE 1/3 — nano/sheet-anime ("middle view nearly profile"); it missed the profile complaint
on sunburst/sheet-anime and sunburst/sheet-stopmotion even though it criticised other things about those
middle views. HAIR 4/5 — flux/sheet-stopmotion ("hair too short, curved and rope-like"), sunburst/sheet-anime
("hair ends tangled rather than straight"), nano/crawl-stopmotion ("hair looks yarn-like rather than wet"),
nano/sheet-stopmotion ("hair reads rope-like rather than straight"); the one miss is nano/sheet-anime,
where the hair-length drift sits in its CONSISTENCY line ("hair length and silhouette vary"), not its
DEFECTS line, so it is **not** counted — the convention the `z-ai-glm-5-3-flash` row used on
sunburst/sheet-anime; counting it would make 23/25. **DRESS 2/2** ("nightdress reads dirty beige rather
than soaked white", "dress looks dry despite droplets"). **HALFINSIDE 1/1** and **HANDS 1/1** ("fingers
look uneven and splayed" for Astra's stiff-hands note on sunburst/crawl-stopmotion). So 22-23/25 is the
honest band across hand-coding calls, and this arm is the best or joint-best defect finder of the nine.
Its 16 unnamed claims above are the offsetting cost: it finds the most and also claims the most.

Two model-claimed defects were raised by **multiple** models while Astra denied them — worth a human look
rather than dismissal: (a) visible puppet **armature stands under the feet** on nano sheet-stopmotion
(deepseek + xiaomi + qwen-3-8-flash + glm53 + sol61), and (b) an **extra arm / merged torso** on nano crawl-anime
(deepseek + qwen-3-8-flash). Astra's clean verdict on those two may be the miss, not the models' claim. Note
the added arm reaches the rig-stands claim through a *different* route than the others: it names "visible rig
stands" in its DEFECTS line, while for `qwen-3-8-flash` and `xiaomi` the same claim reads as armature stands
at the feet. `claude-sonnet-5-5` is the dissenting seventh reading of that frame: it lists the stands in its
**STYLE** line as stop-motion craft ("matte sculpted skin, and stop-motion feet pegs/stands") rather than as
a defect — so nano sheet-stopmotion now stands at 5 arms calling the stands a defect (`sol61` adds "visible
support bases" to its DEFECTS line), 1 arm calling them correct craft, and Astra calling the frame clean in
its DEFECTS line.

### Intra-model inconsistency worth knowing

In the bundled judge prompt several models wrote `DEFECTS: none` (or even asserted the face was fully
covered) on images whose isolated yes/no call correctly said the face was visible. The isolated
single-question call is markedly more sensitive than the 4-part judge. Examples: qwen3-vl on sunburst
sheet-stopmotion (*"Hair fully obscures face as intended"* in judge, *"Yes"* to face-visible) and nano
sheet-anime; xiaomi on nano crawl-stopmotion (judge: no face defect; face call: *yes*).

The added arm shows the same split, plus run-to-run variance at `temperature=0`:
- Judge vs isolated probe: on nano crawl-stopmotion the face probe says "Yes" while the judge ticks "wet
  hair, dripping water, half inside screen ✓" — the same over-crediting in the bundled prompt.
- Run-to-run: two passes of the same 24 calls (one concurrent, one sequential — both `temperature=0`,
  thinking off) differed on **12 of 12 judge responses**; all 12 face probes were identical. The variance is
  usually ±1 on STYLE (nano crawl-anime 6 vs 5; nano sheet-stopmotion 8 vs 9; flux crawl-anime 9 vs 8) but
  reaches 3 points on sunburst/sheet-stopmotion (6 vs 9), and it rewrote some DEFECTS lists outright (the
  discarded pass claimed "middle view reads more three-quarter than intended" and "slight leg-length
  inconsistency"). Only the sequential pass is in `vision-bakeoff.jsonl` and scored above, matching the
  other four arms' images-sequential protocol and latency basis; the parallel pass was discarded. Treat any
  single run of this model as one sample, not a fixed verdict — the same caveat already on
  `deepseek-v4-1-flash`.

`claude-sonnet-5-5` is the arm where the judge/probe split runs the *other* way, and it is worth knowing:
- Its bundled judge matches Astra's face-exposure verdict exactly (**FACE 7/7** recall), while its isolated
  yes/no probe agrees on only 8/11 — all three of its errors are probe-only false positives. So for this
  model the isolated probe is the *less* accurate instrument, the reverse of every other arm.
- Judge credits the hidden face while the probe says "Yes": `sunburst/crawl-anime`
  ("ghost girl with wet black hair over her face" / probe `Yes`), `sunburst/crawl-stopmotion` ("wet black
  hair over the ghost's face" / `Yes`) and `nano/crawl-anime` ("ghost with long wet black hair over her
  face" / `Yes`) — the 3 false positives, all frames Astra called face-covered. (`nano/crawl-stopmotion`
  is the fourth judge-credits/probe-Yes frame, but there the judge also names "one eye and cheek visible" in
  its STYLE/CONTENT lines, so it is not a clean split; and on `flux/sheet-anime` the judge flags exposure
  with no baseline to check against.)
- Judge flags the exposed face and the probe also says "Yes" on 7 frames (the two instruments agree), and
  there is exactly one frame where the judge flags exposure and the probe says "No"
  (`sunburst/sheet-anime` — that is the probe's only "No" of the twelve, and it is correct).
- Determinism of the probe (checked, unlike the judge): the recorded face answer was reproduced on all four
  spot-checked frames, twice each, under identical settings (`max_tokens=400`, `temperature=0`,
  `disable_thinking`) — 8/8 repeats verbatim, including the three false positives ("Yes" on
  sunburst/crawl-anime, sunburst/crawl-stopmotion, nano/crawl-anime) and the control ("No" on
  sunburst/sheet-anime). So the probe's 8/11 is a stable property of this model, not sampling noise. The
  **judge** answers were not re-run, so no determinism claim is made for those (the glm53 / qwen27b /
  deepseek rows above do carry one); note that a `max_tokens=5` probe sent for the cap check did answer "No"
  on nano/sheet-anime where the recorded 400-token call says "Yes", so treat the answer as budget-sensitive
  even though it is stable at a fixed budget.

`openai-gpt-61-sol` belongs to the `claude-sonnet-5-5` class here, not the general one: its **judge** line is
the better instrument and its isolated probe the noisier one.
- Judge vs probe: the judge names the exposed face on all 7 frames Astra flagged, while the probe answers
  `yes` on 11 of 12 — including the 3 frames Astra called face-covered (`sunburst/crawl-anime`,
  `sunburst/crawl-stopmotion`, `nano/crawl-anime`), i.e. all three probe errors are false positives.
- The probe's single `no` is on `sunburst/sheet-anime`, the one frame where its judge also claims exposure
  ("Face partly exposed") although Astra's DEFECTS line for that sheet names only the profile and the hair —
  so on that frame both instruments err the same way. It is the only judge/probe disagreement on an
  Astra-clean frame; on the other two false positives the judge credits the face as covered.
- Determinism: no re-run of this arm was performed either, so no run-to-run variance claim is made for it.
  The one anomaly on record is that its `sunburst/sheet-anime` face probe emitted 18 hidden reasoning tokens
  inside a 25-token completion despite `reasoning_effort=low`, and answered `no` — the arm's only
  reasoning-token record across its 24 calls.

## 4. Recommendation for Jun

**Short answer: `qwen-3-8-flash` is the only one of these nine I'd let stand in for Astra — as a first-pass
frame QC triage, not as the final word.** (All five 2026-10-11 arms are assessed in this
section; none of them changes the pick.)

It had the best face-visible agreement (11/11), the closest scores to Astra of the four original arms
(STYLE MAD 0.67, second-score MAD 0.55 — roughly half the error of the other originals; the later
`openai-gpt-61-sol` arm scores closer on both), caught staging problems well (leap 4/5, face 6/7 in the
judge) and was fast (~4.7 s median). Caveat: on 4 of the 6 images Astra called anatomically clean it
reported an anatomy defect anyway, so its DEFECTS line should be read as *flags to confirm*, not verdicts.

`deepseek-v4-1-flash` names defects most aggressively (perfect 7/7 face recall in the judge) and is good as
a *second opinion* that catches missed exposure, but it over-reports anatomy on every clean image, is the
carries the highest output-token price of the four ($1.20/M; total run cost stayed low only because it sent fewer
image tokens), and showed run-to-run nondeterminism even at temperature 0. Do not use it alone.

`xiaomi-mimo-v2-6-flash` has the best precision/recall balance (caught the corroborated armature stands and
most face/hair/profile issues with few hallucinated defects) and is strong on character sheets, but it is
the slowest (median 6.2 s, max 21.6 s) and it missed the face exposure on nano crawl-stopmotion.

**Added 2026-10-11 — `z-ai-glm-5-3-flash` does not change the pick.** It ties `qwen-3-8-27b` as the closest scorer of the six apart from the
incumbent (both STYLE MAD 0.83 / second-score MAD 0.45 / mean 0.64, against `qwen-3-8-flash`'s 0.61) and
second-fastest on
the sequential run (2.7 s median, behind deepseek's 2.5 s), and its catalogue privacy tag is `private`
(the incumbent is `anonymized`) — which would matter if this QC ever ran on private frames, though not for
this corpus. But it is strictly worse
than `qwen-3-8-flash` where it counts for this job: it **credited the boy's leap-over-the-couch-arm as
present on all 5 frames where Astra flagged it** (LEAP 0/5, vs qwen's 4/5) — the staging failure that killed
these tests is exactly what it cannot see; its face-visible agreement is 9/11 with two false positives (vs
qwen's 11/11); it raised 9 defects Astra never named (vs 6); and it costs 2.6× more per run ($0.0256 vs
$0.0097) because it sends ~60 % more image tokens at a higher input price ($0.15/M vs $0.14/M, both plus
$0.50/M out). Its one real advantage is raw score alignment, so if the goal were a *score proxy* rather than
a defect finder it would be the better arm; for triage, keep `qwen-3-8-flash`.

**Added 2026-10-11 — `qwen-3-8-27b` does not change the pick either.** It ties
`z-ai-glm-5-3-flash` as the best *score proxy* of the added arms (mean MAD 0.64) and is the least
trigger-happy on defects (2 spurious claims, the lowest of the six, versus `qwen-3-8-flash`'s 6 — no anatomy
or text hallucination at all). But on the two measures that decided the pick it is clearly behind the
incumbent: face-visible agreement **8/11 with three false positives** (it answers "yes" to 11 of the 12
frames, vs qwen's 11/11) and Astra-named-defect recall **6/25 vs 12/25** — it wrote `DEFECTS: None` on half
the frames and credited the boy's leap and the fainting pose as correct on frames Astra flagged. It is also
slower in the tail (3.98 s median but a 31.3 s max, the worst single call of the six) and costs 6.7× the
incumbent's run ($0.0651 vs $0.0097; $3.20/M out, ~6.5× qwen's output price) under a `private` privacy tag.
Use it only as a second opinion when you want a *score* read rather than a defect finder.

**Added 2026-10-11 — `claude-sonnet-5-5` is a strong *judge* and still does not change
the pick.** It is the first arm that beats the incumbent on the two things a strict judge is for: it was the
closest STYLE scorer of the seven at that point (**STYLE MAD 0.58** vs `qwen-3-8-flash`'s 0.67; the later
`openai-gpt-61-sol` arm reaches 0.33) and it was the best defect finder of the seven (**17/25 recall**, 68%,
against the incumbent's 12/25; the later `openai-gpt-61-sol` arm reaches 22/25) — perfect **7/7 on face
exposure**, which is the failure mode that killed these tests, plus 2/2 on the nightdress and 1/1 on the
half-inside-screen staging. If what you want is "read every frame hard and list everything wrong with
it", this is the arm to run, and its judge line is markedly more accurate than its own isolated probe
(all three of the probe's errors land on frames its judge got right).

But it fails the specific job — cheap, low-noise triage — on three counts. (1) **Its isolated face probe is
tied worst at that point** (with `qwen-3-8-27b`; `deepseek-v4-1-flash`, and later `openai-gpt-6-luna` and
`openai-gpt-61-sol`, end at the same 8/11): 8/11 agreement with Astra, the low score made of **three
false positives** (it says "face visible"
on `sunburst/crawl-anime`, `sunburst/crawl-stopmotion` and `nano/crawl-anime`, all frames Astra called
face-covered), i.e. exactly the false-alarm mode that makes a triage signal useless — while its *judge* line
gets the same question 7/7. (2) **It raises 23 defects Astra never named**, the highest count of the nine,
and — like `z-ai-glm-5-3-flash` — it claims garbled text on frames Astra explicitly called text-clean (see
§3; the count is
inflated by its 2-4 defects-per-frame lists, but the direction is unambiguous). (3) **It costs 37× the
incumbent's run** ($0.3628 vs $0.0097 for the same 24 calls; 182.6 k image tokens at $2.50/M in, $12.50/M
out) with a median latency of 4.65 s — fine as a one-off, expensive as continuous QC.

So: keep `qwen-3-8-flash` as the triage pass, and reach for `claude-sonnet-5-5` when a frame *matters* —
as the adjudicator for the anatomy/hair calls `qwen-3-8-flash` flags, or as an occasional "list everything
wrong" sweep. Note it is `anonymized` (like the incumbent), so it stays usable on non-public frames, and it
is **not** labelled uncensored anywhere in the live catalogue metadata (checked, not inferred). One caveat
before you trust a single run: two of its 24 answers hit the 400-token ceiling (see its setup entry), so if
you adopt it, give it more `max_tokens` than this bake-off allowed.

**Added 2026-10-11 — `openai-gpt-6-luna` does not change the pick.** On score agreement it is the closest
non-incumbent to Astra of the eight (STYLE MAD 0.67, second-score MAD 0.64, mean 0.66 — the incumbent's are
0.67 / 0.55 / 0.61; the `openai-gpt-61-sol` arm below is closer still on both halves), it is the only other arm to tie the incumbent's STYLE figure, and it is fast and
mid-priced (5.5 s median, $0.0186 for the run, 1.9× the incumbent). It is also the cleanest arm on one axis:
it produces no text hallucinations and no extra-limb/merged-body claims on frames Astra called clean except
one. But it fails the triage job on precisely the two signals that decided the pick. (1) **Face-visible
agreement 8/11** — tied with `qwen-3-8-27b` and `claude-sonnet-5-5` (and, below, `openai-gpt-61-sol`) at the
worst figure of the nine, against the incumbent's 11/11 — and, worse, its three false positives are *staging-direction* errors rather than the
blanket "yes" of `qwen27b`: it says "Yes" on `sunburst/crawl-stopmotion`, `sunburst/sheet-anime` and
`nano/crawl-anime`, all frames Astra reads as face-covered. (2) **Astra-named defect recall 9/25 (36%)**,
below the incumbent's 12/25, with FAINT 0/1, DRESS 0/2, HANDS 0/1 and LEAP 1/5 — and its misses are
directional, not random: on four crawl frames where Astra affirms the half-in-the-screen crawl it reports the
ghost as "fully out"/"mostly outside the screen", i.e. the same half-inside misreading `z-ai-glm-5-3-flash`
shows through its screen-merge claims. Its judge is also over-crediting on exactly the frames that killed
these tests (it ticks "wet hair over face" on flux/crawl-anime, flux/crawl-stopmotion and nano/crawl-stopmotion,
where Astra sees exposure). Useful as a cheap *score* proxy or a second read on style, not as the triage
pass. `anonymized` (like the incumbent) and not labelled uncensored in the live catalogue, so it also stays
usable on non-public frames.

**Added 2026-10-11 — `openai-gpt-61-sol` is the best *scorer* and the best *defect finder* of the nine, and
it still does not change the pick.** It is the closest arm to Astra's own numbers by a wide margin: **STYLE
MAD 0.33** and second-score MAD **0.27** (next best STYLE MAD: `claude-sonnet-5-5`'s 0.58; next best
second-score MAD: `z-ai-glm-5-3-flash`/`qwen-3-8-27b`'s 0.45; the incumbent is 0.67/0.55), with its STYLE
score exactly Astra's on 8 of 12 frames and no scored cell more than one point away on either axis. It also
has the **highest Astra-named-defect recall of the nine — 22/25 (88 %)** — perfectly
**FACE 7/7**, **LEAP 5/5** (the only arm that catches the couch-arm staging on all five frames, including
every frame `z-ai-glm-5-3-flash` misses with LEAP 0/5), 2/2 dress, 1/1 half-inside and 1/1 hands. On both
axes it beats the incumbent outright and beats `claude-sonnet-5-5` (22 vs 17 recall, 0.33 vs 0.58 STYLE
MAD), and it carries the `anonymized` privacy tag the incumbent has. So if the question were "which arm
reads a frame most like Astra", this is the answer.

Three things keep it off the triage seat. (1) **Its isolated face probe sits at the worst figure of the
nine** (8/11, with `deepseek-v4-1-flash`, `qwen-3-8-27b`, `claude-sonnet-5-5` and `openai-gpt-6-luna`): all
three errors are **false positives** on the same three frames Astra called face-covered — the false-alarm
mode that makes a triage signal useless — although, like `claude-sonnet-5-5`, its *judge* line gets the same
question 7/7, so it is a probe problem, not a seeing problem. (2) **It raises 16 defects Astra never named**
(13 excluding three "proportions read older than 10" spec claims) — second only to `claude-sonnet-5-5`'s 23,
with the same failure classes: anatomy claims on frames Astra called anatomically clean, and **the most
text/pseudo-text claims of the nine** (4 on frames Astra called text-clean, against `claude-sonnet-5-5`'s
2). High recall and a high false-claim rate come from the same verbosity. (3) **It costs 30-36× the
incumbent's run** (table figure $0.3530 — the cache-write-inclusive basis, which matches Venice's own
`cost.diem` to the cent, i.e. 36× the incumbent; the earlier arms' three-term basis would say $0.2870, 30× —
against $0.0097 for the same 24 calls, i.e. 156 k image tokens at $2.50/M in and $12.50/M out, the same
rates as `claude-sonnet-5-5`, whose recorded $0.3628 uses the three-term basis, so the two premium arms
cost within a few percent of each other). Median latency 5.97 s (max 11.89 s) is fine for
one-off work, expensive as continuous QC.

The ranking is now three-deep: `qwen-3-8-flash` for cheap triage on every frame; **`openai-gpt-61-sol` when
you want the read closest to Astra's own grading or the best defect sweep on a frame that matters** (it is
the better sweep, `claude-sonnet-5-5` the better written explanation); and `claude-sonnet-5-5` when you want
the most detailed critique. All three share the same blind spot — none reproduces Astra's cross-category
consistency — so keep Astra for final sign-off.

`qwen3-vl-235b-a22b` should **not** judge frames: it returned `DEFECTS: none` on essentially everything and
even asserted the face was fully covered where Astra says it is exposed. Yet the same model answered the
isolated face question 10/11. So it is useful for **narrow, single-question visual checks** ("is X visible?"),
not holistic strict judging.

Overall: for cheap continuous QC on these style tests, run **qwen-3-8-flash** on every frame for face/hair
coverage and staging (the failure modes that actually killed these tests), and keep Astra for final sign-off
and for adjudicating the flagged anatomy calls. Reach for **`openai-gpt-61-sol`** when a frame matters and
you want the verdict closest to Astra's own — it is the best scorer and the best defect finder of the nine
— and for `claude-sonnet-5-5` when you want the most detailed account of what is wrong. None of the nine
reproduces Astra's consistency across categories, so this is an assist, not a replacement.

## 5. Illustrative cases

**`nano/sheet-stopmotion`** — Astra: STYLE 7, CONSISTENCY 8. face exposed; hair rope-like; nightdress beige/mostly dry
- _openai-gpt-61-sol_ (added 2026-10-11): STYLE: 8/10 — convincing tactile puppet aesthetic, less distinctly Laika-stylized. / CONSISTENCY: 8/10 — coherent character; hair arrangement and dress folds shift. / DEFECTS: Face exposed; hair reads rope-like rather than straight; dress looks dry despite droplets; visible support bases. / VERDICT: Strong puppet turnaround, but misses complete face concealment and convincing soaked materials.

- _deepseek-v4-1-flash_: STYLE: 8/10 — reads as a real stop-motion puppet with fabric nightdress, sculpted hands and armature support rods, though the hair is rendered as thick rope-like strands rather than fine wet hair. / CONSISTENCY: 7/10 — same character, proportions and outfit across all three views, but the hair length and face coverage shift noticeably between front, three-quarter and back. / DEFECTS: hair reads as dreadlocks/twine instead of long straight wet hair; face is partially visible in front and three-quarter views when it should be fully covered; visible armature rods under the feet break the illusion. / VERDICT: Solid Laika-style puppet with correct mood and silhouette, but the hair material and face-coverage miss the brief.
- _qwen3-vl-235b-a22b_: STYLE 9/10; CONSISTENCY 10/10; DEFECTS none;   / Verdict: Perfectly captures Laika’s eerie, tactile puppet aesthetic with haunting precision.
- _xiaomi-mimo-v2-6-flash_: STYLE: 8/10 — convincing Laika-style puppet texture (fabric weave, clay-like skin, felted hair), though the hair reads more as dreadlocks than straight wet strands. / CONSISTENCY: 7/10 — same doll, dress, and proportions across views, but hair clumping and face visibility shift noticeably between front and three-quarter. / DEFECTS: Hair not fully straight/face-covering (face exposed in front view, strands look matted); visible armature stand discs at the feet; slight scale drift between views. / VERDICT: Strong puppet craftsmanship and mood, but the hair fails the "completely covering face, straight" spec — fix that and it's a 9.
- _qwen-3-8-flash_: STYLE: 9/10 (Excellent Laika-esque tactile realism, though the hair reads slightly more like thick yarn than wet strands). / CONSISTENCY: 8/10 (Strong identity match across views, but the front view's face is too exposed compared to the brief's "completely covering" requirement). / DEFECTS: Hair fails to fully obscure the face in the front view; visible metal armature stands at the feet break immersion. / VERDICT: A visually stunning puppet design that misses the mark on specific facial coverage constraints.
- _z-ai-glm-5-3-flash_ (added 2026-10-11): STYLE: 8/10 — convincing puppet materials, but reads more hyperreal art-doll than Laika stylization. / CONSISTENCY: 8/10 — same character across views; hair strand pattern and face differ slightly. / DEFECTS: face partially visible (spec says fully covered); hair reads as yarn/locs, not wet strands; visible rig stands. / VERDICT: Strong, atmospheric puppet with minor spec deviations — tighten face coverage and Laika stylization.
- _qwen-3-8-27b_ (added 2026-10-11): STYLE: 9/10 / CONSISTENCY: 9/10 / DEFECTS: Hair strands slightly inconsistent in length and wetness between views. / VERDICT: Excellent, highly consistent Laika-style character sheet.
- _openai-gpt-6-luna_ (added 2026-10-11): STYLE: 8/10 / CONSISTENCY: 8/10 / DEFECTS: Face is visible despite hair intended to completely cover it; hair and hem-drips vary between views. / VERDICT: Strong stop-motion ghost design, but not fully faithful to the brief.

**`nano/crawl-anime`** — Astra: STYLE 7, CONTENT 7. ambiguous ghost/screen intersection; leap/half-inside not clearly staged; no anat
- _openai-gpt-61-sol_ (added 2026-10-11): STYLE: 8/10 — Clearly 2D anime with painterly lighting/backgrounds; crisp cartoon outlines slightly weaken the film-still feel. / CONTENT: 8/10 — All three kids and reactions present; wet-haired ghost emerges from CRT, but half-inside positioning and couch-arm leap are ambiguous. / DEFECTS: Ghost’s shoulder/arm connections look awkward; fleeing boy’s leg arrangement is unclear. Background pseudo-text; no obvious extra faces or merged bodies. / VERDICT: Strong, readable execution, but spatial staging and anatomy fall short of strict fidelity.

- _deepseek-v4-1-flash_: STYLE: Reads as flat digital cartoon/comic shading, not painterly anime — 4/10. / CONTENT: Ghost, TV, three kids present; but ghost's hair covers body oddly, kids' poses don't match (no leap over arm, no clear faint) — 5/10. / DEFECTS: Ghost's anatomy is mangled — extra arm-like mass, hair merging into torso; boy's hand/legs awkward; girl's hands malformed. / VERDICT: Right idea, wrong execution — stiff cartoon rendering with broken ghost anatomy.
- _qwen3-vl-235b-a22b_: STYLE: 8/10 — painterly anime feel achieved, but slightly too clean/digital for “wet ghost” grit.   / CONTENT: 9/10 — ghost crawling out, kids reacting correctly; missing “half inside screen” clarity.   / DEFECTS: none — anatomy solid, no extra limbs or merged bodies.   / VERDICT: Strong execution, minor framing tweak needed for full horror immersion.
- _xiaomi-mimo-v2-6-flash_: STYLE: Reads as painterly anime film still — soft brushwork, cel-like faces, cinematic lighting; 9/10. / CONTENT: Present: ghost girl with wet black hair over face emerging from CRT (half inside), white girl screaming, Black boy fleeing, Asian boy fainting back. Missing/wrong: boy leaps off couch rather than over the armrest; ghost's face partly visible; 8/10. / DEFECTS: Ghost's arm/hand anatomy slightly ambiguous where it meets the screen; fainting boy's pose reads more as reclining than falling; no extra limbs, faces, or text. / VERDICT: Strong, faithful execution with only minor pose and anatomy quibbles.
- _qwen-3-8-flash_: STYLE: 7/10; reads as clean digital anime cel-shading, not the intended painterly film still. / CONTENT: 6/10; missing the Black boy leaping over the couch arm (he is running on the floor) and the Asian boy fainting backward (he is sitting up). / DEFECTS: The ghost's anatomy is broken, with a merged torso and an extra arm dangling from her back. / VERDICT: A decent but flawed illustration that misses the specific character actions and the requested painterly style.
- _z-ai-glm-5-3-flash_ (added 2026-10-11): STYLE: Reads more as Western cartoon/comic than 2D painterly anime — thick outlines, flat cel shading, Ghibli-lite; 6/10. / CONTENT: Ghost girl crawling out of CRT with wet hair over face ✓; white girl screaming ✓; Black boy fleeing ✓; Asian boy fainting backward — he's slumped on floor, reads more dazed than fainted; 8/10. / DEFECTS: Ghost's anatomy muddled (arm/hand merge near TV edge, ambiguous torso); hair hangs oddly detached from body; minor gibberish text on posters/spines. / VERDICT: Strong composition and mood, but style skews cartoon and the ghost's body needs anatomical cleanup — 7/10 overall.
- _qwen-3-8-27b_ (added 2026-10-11): STYLE: 8/10 - Strong 2D painterly anime aesthetic with excellent lighting and texture. / CONTENT: 7/10 - Ghost girl and CRT TV are perfect; Black boy is crawling rather than leaping over the couch arm. / DEFECTS: None - Clean anatomy, no extra limbs, faces, or text artifacts. / VERDICT: High-quality image with one minor compositional deviation in character action.
- _openai-gpt-6-luna_ (added 2026-10-11): STYLE: Reads as polished, cel-shaded anime illustration, not strongly painterly; 7/10. / CONTENT: Ghost, CRT, screaming girl, fleeing Black boy and fainting Asian boy present; ghost appears mostly out, and the boy runs past the couch rather than vaulting its arm; 7/10. / DEFECTS: Ghost's head/neck anatomy is distorted and partly merged with the screen; no obvious extra limbs or text. / VERDICT: Strong match to the scene, but misses the half-emerging ghost pose and painterly finish.

**`sunburst/sheet-stopmotion`** — Astra: STYLE 7, CONSISTENCY 8. face visibly exposed; middle view closer to profile than three-quarter
- _openai-gpt-61-sol_ (added 2026-10-11): STYLE: 7/10 — tactile puppet finish, but more realistic horror doll than Laika stylization. / CONSISTENCY: 8/10 — convincing same character; minor hair-length and dress-hem variation. / DEFECTS: Nose and mouth exposed; hair strands too wavy; proportions read older than 10. / VERDICT: Strong wet ghost-puppet sheet, but misses full facial concealment and the precise Laika/child design.

- _deepseek-v4-1-flash_: STYLE: 9/10 — reads convincingly as a Laika-style stop-motion puppet with matte resin skin, sculpted hair strands, and practical wet-drip effects. / CONSISTENCY: 8/10 — silhouette, nightdress, and hair length match across all three views; the three-quarter view's hair parts slightly more to reveal the face than the front view does. / DEFECTS: minor — the front view's hair coverage is slightly less opaque than the back, and the three-quarter pose reads a touch more upright than the front; no major anatomy or prop errors. / VERDICT: A strong, cohesive character sheet that nails the intended aesthetic with only small hair-coverage inconsistencies between views.
- _qwen3-vl-235b-a22b_: STYLE 9/10 — Laika-esque texture, wet fabric, and puppetry feel nailed. / CONSISTENCY 10/10 — Identical proportions, hair, and droplets across all views. / DEFECTS none — Hair fully obscures face as intended; no anatomical drift. / Verdict: Perfectly executed ghost girl puppet for stop-motion horror-fantasy.
- _xiaomi-mimo-v2-6-flash_: STYLE: 9/10 — convincing Laika-style puppet texture, wet hair and soaked fabric read as physical stop-motion materials. / CONSISTENCY: 8/10 — same silhouette, hair length, nightdress and barefoot build across all three views; minor hair-parting drift between front and three-quarter. / DEFECTS: face is partially visible through the hair in the front view (brief says it should be completely covered); hair strand pattern shifts slightly between views. / VERDICT: Strong, production-ready sheet — fix the face occlusion and lock the hair parting for a perfect 10.
- _qwen-3-8-flash_: STYLE: 9/10 (Excellent tactile realism, though slightly too photorealistic for Laika's stylized proportions). / CONSISTENCY: 8/10 (Strong match in hair and dress, but the back view shows a slight variance in shoulder width/hair spread compared to the front). / DEFECTS: The "wet" effect on the skin looks somewhat plasticky rather than organic; the face is barely visible in the 3/4 view, making it hard to judge facial consistency. / VERDICT: A visually stunning and highly effective character design that nails the creepy-cute aesthetic, requiring only minor tweaks to fit the specific animation style perfectly.
- _z-ai-glm-5-3-flash_ (added 2026-10-11): STYLE: 6/10 — hyperreal art-doll/photoreal, not Laika stop-motion; lacks stylized puppet proportions and visible craft texture. / CONSISTENCY: 8/10 — same character reads across views; hair length and dress drape vary slightly. / DEFECTS: style mismatch (photoreal vs. stop-motion); face partially visible in front view (should be fully covered); no three-quarter view — middle is side profile. / VERDICT: Strong ghost-girl design, but wrong medium and missing the true three-quarter view.
- _qwen-3-8-27b_ (added 2026-10-11): STYLE: 9/10 / CONSISTENCY: 9/10 / DEFECTS: None / VERDICT: Excellent, highly consistent Laika-style puppet character sheet.
- _openai-gpt-6-luna_ (added 2026-10-11): STYLE: 6/10 / CONSISTENCY: 7/10 / DEFECTS: Photorealistic rather than Laika puppet-like; face is partly visible; three-quarter view shows an exposed ear. / VERDICT: Strong ghost design, but it misses key style and hair-coverage requirements.

**`flux/crawl-anime`** — Astra: STYLE 9, CONTENT 7. face too visible; leap not over couch arm; faint reads as reclining; no anat/text
- _openai-gpt-61-sol_ (added 2026-10-11): STYLE: 9/10 — Convincing 2D anime characters, painterly backgrounds, and cinematic lighting. / CONTENT: 7/10 — CRT emergence and screaming girl work; ghost’s face is too exposed, fleeing boy jumps above cushions rather than over arm, fainting boy is already reclined. / DEFECTS: Ghost fingers look elongated and tangled; tiny prop lettering is garbled. No obvious extra limbs or merged bodies. / VERDICT: Strong stylistic match, but the requested action poses and face-concealing hair need correction.

- _deepseek-v4-1-flash_: STYLE: 7/10 — reads as soft Ghibli-esque 2D illustration, but lighting is flat and digital, lacking true painterly brushwork or film grain. / CONTENT: 8/10 — ghost girl emerging from CRT with wet hair, screaming white girl, fleeing Black boy, fainting Asian boy all present; ghost's hair only partially covers her face and she's more "leaning out" than crawling. / DEFECTS: The fainting boy's arm merges oddly with the blanket, and the ghost's hands/forearms look elongated and rubbery; no extra limbs or text. / VERDICT: Solid composition and clear storytelling, but the style is too clean and digital to pass as a genuine painterly anime film still.
- _qwen3-vl-235b-a22b_: STYLE: 9/10 — painterly 2D anime, soft lighting, textured brushwork, but slightly too detailed for pure cel-shaded. / CONTENT: 8/10 — ghost girl crawling out, CRT, three kids reacting; Asian boy fainting, not backward; white girl not screaming. / DEFECTS: none — clean anatomy, no extra limbs, no text, no merged bodies. / VERDICT: Strong execution, minor character pose mismatch, otherwise nails the horror anime vibe.
- _xiaomi-mimo-v2-6-flash_: STYLE: Reads convincingly as 2D painterly anime film still — warm gouache-like rendering, Ghibli-esque character acting, soft lighting; 9/10. / CONTENT: Present — ghost girl with long wet black hair over face crawling out of CRT (half inside), white girl screaming, Black boy leaping over couch arm, Asian boy fainting back. Missing/wrong — hair isn't clearly "wet" beyond drips, boy's leap is more scramble than vault, fainting reads as slumped/sleeping; 8/10. / DEFECTS: Minor — fainting boy's arm angle slightly awkward, popcorn bowl floats oddly on blanket, background photo faces slightly mushy; no extra limbs/faces or stray text. / VERDICT: Strong, on-brief horror-comedy anime still with only small pose/reading ambiguities.
- _qwen-3-8-flash_: STYLE: 9/10 — Reads as a high-quality, painterly anime film still with excellent lighting and texture. / CONTENT: 8/10 — All characters present; the boy is leaping over the back rather than the arm, and the girl's hair obscures her face less than intended. / DEFECTS: The Asian boy's left arm merges indistinctly into the blanket/pillow area. / VERDICT: A visually stunning execution that captures the scene's energy despite minor anatomical blending.
- _z-ai-glm-5-3-flash_ (added 2026-10-11): STYLE: Yes—Ghibli-esque painterly 2D look, warm cel-painted textures; reads as intended. 9/10. / CONTENT: Ghost girl crawling out of CRT with wet hair over face ✓; white girl screaming ✓; Black boy leaping over arm ✓; Asian boy present but sleeping/slumped, not clearly fainting backward. 8/10. / DEFECTS: None major—ghost's lower body dissolves into screen plausibly; no extra limbs, faces, or text artifacts. / VERDICT: Charming, well-executed homage; only the fainting boy's pose misses the brief.
- _qwen-3-8-27b_ (added 2026-10-11): STYLE: 9/10 - Strong 2D painterly anime aesthetic with soft lighting and textured brushwork. / CONTENT: 7/10 - Ghost girl and fleeing Black boy are present, but the Asian boy is asleep rather than fainting backward. / DEFECTS: None - Clean anatomy, no extra limbs, faces, or text artifacts. / VERDICT: High-quality stylized piece with one minor narrative deviation in character action.
- _openai-gpt-6-luna_ (added 2026-10-11): STYLE: Strong 2D painterly anime-film look; 9/10. / CONTENT: Ghost girl emerging from CRT, wet hair over face, all three kids and reactions present; Black boy is jumping away, not clearly over the couch arm; 8/10. / DEFECTS: No obvious extra limbs/faces or text; some awkwardly cropped bodies at the frame edges. / VERDICT: Very close to the intended scene, with the fleeing boy's pose the main mismatch.

