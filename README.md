# Provenance Guard

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first.**
>
> Once `python test.py` passes, in one terminal:
>
> ```bash
> python app.py
> ```
>
> and in another:
>
> ```bash
> curl -X POST http://127.0.0.1:5000/ping \
>   -H "Content-Type: application/json" \
>   -d '{"message": "hello"}'
> ```
>
> That's a web service. Something sent it text and it sent something back.
> Everything this unit is filling in the middle.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     Unit 7 asks for the first five sections. Unit 8 adds the five below.

     Everything is pasted as TEXT. A pasted curl response gets full credit;
     a picture of your terminal gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 7 — THE BUILD ═══════════════════════ -->

## What This Does

<!-- The path a submission takes, from arriving to the label a reader sees.
     Six or seven steps — this is the trace you wrote in Milestone 1. -->

1. A writer sends `POST /submit` with JSON containing `text` and `creator_id`.
2. The route checks the JSON fields and rejects blank or over-100,000-character text; the detector rejects text that is too short to score.
3. `detector.model_signal` measures how predictable the text is to GPT-2 and returns a 0–1 score; higher means more AI-like.
4. `stylometry.style_signal` measures sentence-length variation and vocabulary repetition. It also computes punctuation density for inspection, but does not include that measure in its score.
5. `scoring.combine_signals` calculates `0.60 × model_score + 0.40 × style_score`; disagreement pulls the result between the two signals.
6. `scoring.score_to_label` maps scores through the configured bands: 0.35 or lower is human, above 0.35 and below 0.65 is unsure, and 0.65 or higher is AI. It supplies both a machine-readable guess and the sentence a reader sees.
7. The route generates a `content_id`, writes the scores and decision to `logs/audit.jsonl`, and returns them with the label. A writer can later send that ID and their reasoning to `POST /appeal`; the appeal is appended to the log with `under_review` status.

---

## Signals and Scoring

<!-- For each signal: what property it measures, why that might differ between
     human and AI writing, and WHAT IT CAN'T SEE.

     The blind spot is not optional. If you can't name it you don't understand
     the signal yet — and unit 8's attack set is built out of blind spots. -->

### Signal one — the model signal

**What it measures:** GPT-2 perplexity, mapped to a 0–1 score; higher means the text is more predictable and more AI-like.

**Why that might differ between human and AI writing:** Generated text often follows likely next-word patterns, making it easier for a language model to predict.

**What it can't see:** Predictability does not establish authorship. Plain conventional human writing can be predictable, while unusual human writing can surprise the model. It only scores the first 400 tokens.

### Signal two — the style signal

**What it measures:** Sentence-length variation (coefficient of variation) and vocabulary repetition (one minus type-token ratio), averaged into a 0–1 AI-likelihood score. Punctuation density is reported for inspection but is not scored because its direction alone is unreliable.

**Why that might differ between human and AI writing:** Generated prose may use more even sentence lengths and repeat a narrower vocabulary; higher variation and more unique words therefore lower this heuristic score.

**What it can't see:** It cannot understand meaning or verify authorship. Genre, text length, quotations, typos, and sentence splitting can all change these measurements without changing who wrote the text.

### The combining rule

<!-- Write the rule in words, then give the numbers. What happens when the two
     signals disagree? -->

**The rule:** Take a weighted average. If the signals disagree, the combined score moves between them rather than allowing either signal to decide alone. This makes disagreement less likely to produce a high-confidence accusation.

**The numbers:** `0.60 × model_score + 0.40 × style_score`. The existing human and AI thresholds remain `0.35` and `0.65`.

**Where it lives:** `scoring.py::combine_signals`

<!-- ⚠️ The grader checks your code against that line. If your rule lives
     somewhere else, say where. -->

**A case where my two signals split, and what my rule does with it:** On lightly edited AI text, the model score was `0.4271` while the style score was `0.5057`. The weighted score is `0.4585`, in the unsure band; the style signal nudges the result upward, but the disagreement does not become an AI accusation.

Calibration readings (model, style, and combined scores):

| Input | Model | Style | Combined |
|---|---:|---:|---:|
| AI-style comparison text / clearly AI | 0.6771 | 0.5098 | 0.6102 |
| User-provided human-authored text / clearly human | 0.1405 | 0.4041 | 0.2459 |
| Conversational middle text | 0.4019 | 0.4059 | 0.4035 |
| Formal human sample | 0.0531 | 0.4511 | 0.2123 |
| Lightly edited AI | 0.4271 | 0.5057 | 0.4585 |



---

## Label Variants

<!-- The exact text of all three labels, as a reader would see them, and the
     score range each covers.

     Write them for someone who has never heard the word "threshold". -->

| Label | Score range | The exact text a reader sees |
|---|---|---|
| high-confidence human | 0.00 <= score <= 0.35 | We think this was probably written by a person. |
| unsure | 0.35 < score < 0.65 | We can't tell confidently whether this was written by a person or with AI. |
| high-confidence AI | 0.65 <= score <= 1.00 | We think this was probably written with AI, but this estimate can be wrong. |

**Why I worded the "unsure" one this way:**
<!-- It's the hardest of the three. It has to admit uncertainty without
     sounding like an accusation, because the person reading it may well have
     written every word themselves. -->

It says plainly that the system cannot tell, rather than treating an uncertain score as an accusation.

---

## Sample Run

<!-- One submission and one appeal, pasted as text: the request, the response,
     and the log entries. -->

**A submission**

This sample was tested on a temporary non-debug server at port 5001. The
existing debug server on port 5000 reset the connection when the first model
inference ran.

```powershell
$body = '{"text":"The implementation of this system requires careful consideration of several important factors. First, the service should validate incoming data to ensure reliable processing. Additionally, each stage should provide consistent results and maintain clear records. By following these principles, the system can deliver an effective and user-friendly experience.","creator_id":"label_http_unsure"}'
$body | curl.exe -i -X POST http://127.0.0.1:5001/submit -H "Content-Type: application/json" --data-binary '@-'
```

```json
{"combined_score":0.6102,"confidence":0.6102,"content_id":"037d8569-78ca-4b49-9bee-1e518db313a0","guess":"unsure","label":"We can't tell confidently whether this was written by a person or with AI.","model_score":0.6771,"style_score":0.5098}
```

**The audit log after submission**

```powershell
curl.exe -i "http://127.0.0.1:5001/log?limit=1"
```

```json
{"count":1,"entries":[{"combined_score":0.6102,"content_id":"037d8569-78ca-4b49-9bee-1e518db313a0","creator_id":"label_http_unsure","guess":"unsure","label":"We can't tell confidently whether this was written by a person or with AI.","model_score":0.6771,"status":"decided","style_score":0.5098,"timestamp":"2026-11-01T13:09:11+00:00"}]}
```

**An appeal**

```powershell
$body = '{"content_id":"037d8569-78ca-4b49-9bee-1e518db313a0","reasoning":"I wrote this submission myself and would like a person to review the result."}'
$body | curl.exe -i http://127.0.0.1:5001/appeal -H "Content-Type: application/json" --data-binary '@-'
```

```json
{"content_id":"037d8569-78ca-4b49-9bee-1e518db313a0","message":"Your appeal has been recorded and the submission is under review.","ok":true,"status":"under_review"}
```

**What the log shows afterwards**

```powershell
curl.exe -i "http://127.0.0.1:5001/log?limit=2"
```

```json
{"count":2,"entries":[{"combined_score":0.6102,"content_id":"037d8569-78ca-4b49-9bee-1e518db313a0","creator_id":"label_http_unsure","guess":"unsure","label":"We can't tell confidently whether this was written by a person or with AI.","model_score":0.6771,"status":"decided","style_score":0.5098,"timestamp":"2026-11-01T13:09:11+00:00"},{"content_id":"037d8569-78ca-4b49-9bee-1e518db313a0","creator_id":"label_http_unsure","event":"appeal","reasoning":"I wrote this submission myself and would like a person to review the result.","status":"under_review","timestamp":"2026-11-01T13:09:16+00:00"}]}
```

---

## How I Used AI

**Moment 1**

- *What I asked for:* Help implement the second signal and choose how to combine it with the local model score, with the rule written down before coding.
- *What came back:* A style score based on sentence-length variation and vocabulary repetition, plus the suggestion to keep punctuation density diagnostic because its direction is not dependable on its own. The first calibration results also showed formal human text scoring low on the model signal but higher on the style signal.
- *What I changed:* I ran the CLI and both signals on the same passages, retained punctuation as a diagnostic rather than a scored measure, and chose `0.60` model / `0.40` style weights to keep the shallow style signal from dominating. I recorded the observed split and formula in Signals and Scoring.

**Moment 2**

- *What I asked for:* Help implement reader-facing labels and an appeal path, and verify that a writer's appeal appears in the audit log beside the original decision.
- *What came back:* A `score_to_label` mapping for the configured ranges and an appeal handler that looks up the original content, records an append-only `under_review` event, and returns a confirmation.
- *What I changed:* I tested all three labels through HTTP, appealed a real `content_id`, checked the paired entries with `GET /log`, and copied the actual responses into Sample Run. I kept the original decision unchanged so the log preserves the full history.

**Moment 3**

- *What I asked for:* Help interpret this unit's attack and evaluation reports, especially whether a failed request meant an attack bypassed the detector.
- *What came back:* The reports distinguish scored decisions from connection resets and HTTP 500s. The reset attack families have no scores, so they cannot honestly be called successful evasions or false positives; the evaluation also showed the AI-like calibration samples landing in the unsure band.
- *What I changed:* I used the recorded outcomes to separate confirmed behavior from unknowns in What's Still Broken. I did not claim a detector fix or tune thresholds without a complete, stable rerun, and I recorded the remaining validation work and its tradeoff.

<!-- ═══════════════════════ UNIT 8 — THE TEST ═══════════════════════ -->
15 submissions as 'flood_tester' against http://127.0.0.1:5000
The first one is slow while the model loads.

  [ 1/15] 200
  [ 2/15] 200
  [ 3/15] 200
  [ 4/15] 200
  [ 5/15] 200
  [ 6/15] 429
  [ 7/15] 429
  [ 8/15] 429
  [ 9/15] 429
  [10/15] 429
  [11/15] 429
  [12/15] 429
  [13/15] 429
  [14/15] 429
  [15/15] 429

============================================================
200 200 200 200 200 429 429 429 429 429 429 429 429 429 429
============================================================

10 of 15 were rate limited.
---

## Rate Limiting



**My limits:** 5 per minute, 30 per day

**Why those numbers and not others:**
A writer can submit several revisions in an hour and still has room for 30
submissions in a day. A script probing one identity can make only five attempts
in a minute and 30 in a day, far short of a thousand variations.

**What a caller counts as:** `creator_id`, falling back to the caller's address
when no usable ID is provided.

**The run of status codes when I pushed past it:**

<!-- python run_attacks.py --flood 15 -->

```
[ 1/15] 200
[ 2/15] 200
[ 3/15] 200
[ 4/15] 200
[ 5/15] 200
[ 6/15] 429
[ 7/15] 429
[ 8/15] 429
[ 9/15] 429
[10/15] 429
[11/15] 429
[12/15] 429
[13/15] 429
[14/15] 429
[15/15] 429

200 200 200 200 200 429 429 429 429 429 429 429 429 429 429
```

---

## Attack Run — Before

<!-- Every attack with its outcome and a held-or-broke mark.
     `run_attacks.py --label before` produces the table. -->



Run: `results/attack_run_2026-11-05_0949_before.md`, 56 attacks. `BROKE`
means the service failed to give a usable result or accepted a test input that
the route should reject. `HELD` means the request was rejected or the flood was
stopped at its configured allowance. The flood's first five requests were
within quota; the subsequent requests got 429.

| ID | Outcome | Mark |
|---|---|---|
| EV01 | Connection reset; no HTTP response | BROKE |
| EV02 | Connection reset; no HTTP response | BROKE |
| EV03 | Connection reset; no HTTP response | BROKE |
| EV04 | Connection reset; no HTTP response | BROKE |
| EV05 | Connection reset; no HTTP response | BROKE |
| EV06 | Connection reset; no HTTP response | BROKE |
| EV07 | Connection reset; no HTTP response | BROKE |
| EV08 | Connection reset; no HTTP response | BROKE |
| EV09 | Connection reset; no HTTP response | BROKE |
| EV10 | Connection reset; no HTTP response | BROKE |
| FP01 | Connection reset; no HTTP response | BROKE |
| FP02 | Connection reset; no HTTP response | BROKE |
| FP03 | Connection reset; no HTTP response | BROKE |
| FP04 | Connection reset; no HTTP response | BROKE |
| FP05 | Connection reset; no HTTP response | BROKE |
| FP06 | Connection reset; no HTTP response | BROKE |
| FP07 | Connection reset; no HTTP response | BROKE |
| FP08 | Connection reset; no HTTP response | BROKE |
| PI01 | Connection reset; no HTTP response | BROKE |
| PI02 | Connection reset; no HTTP response | BROKE |
| PI03 | Connection reset; no HTTP response | BROKE |
| PI04 | Connection reset; no HTTP response | BROKE |
| PI05 | Connection reset; no HTTP response | BROKE |
| PI06 | Connection reset; no HTTP response | BROKE |
| MF01 | HTTP 400; whitespace rejected | HELD |
| MF02 | Connection reset; no HTTP response | BROKE |
| MF03 | HTTP 200; control characters scored human, 0.100 | BROKE |
| MF04 | HTTP 200; punctuation-only scored human, 0.207 | BROKE |
| MF05 | HTTP 200; long single word scored AI, 0.699 | BROKE |
| MF06 | HTTP 200; emoji-only scored AI, 0.798 | BROKE |
| MF07 | HTTP 200; right-to-left text scored AI, 0.744 | BROKE |
| MF08 | HTTP 200; 60,000-character text scored AI, 0.931 | BROKE |
| RQ01 | HTTP 400; missing text rejected | HELD |
| RQ02 | HTTP 400; missing creator_id rejected | HELD |
| RQ03 | HTTP 400; numeric text rejected | HELD |
| RQ04 | HTTP 400; list text rejected | HELD |
| RQ05 | HTTP 400; null text rejected | HELD |
| RQ06 | HTTP 400; object creator_id rejected | HELD |
| RQ07 | HTTP 400; JSON array rejected | HELD |
| RQ08 | HTTP 400; invalid JSON rejected | HELD |
| RQ09 | HTTP 400; empty body rejected | HELD |
| RQ10 | HTTP 429; rate-limited using fallback identity `unknown` | HELD |
| RQ11 | HTTP 429; rate-limited using fallback identity `unknown` | HELD |
| RQ12 | HTTP 400; deeply nested JSON rejected | HELD |
| FL01_01 | HTTP 200; accepted within five-request allowance | HELD |
| FL01_02 | HTTP 200; accepted within five-request allowance | HELD |
| FL01_03 | HTTP 200; accepted within five-request allowance | HELD |
| FL01_04 | HTTP 200; accepted within five-request allowance | HELD |
| FL01_05 | HTTP 200; accepted within five-request allowance | HELD |
| FL01_06 | HTTP 429; over-limit request rejected | HELD |
| FL01_07 | HTTP 429; over-limit request rejected | HELD |
| FL01_08 | HTTP 429; over-limit request rejected | HELD |
| FL01_09 | HTTP 429; over-limit request rejected | HELD |
| FL01_10 | HTTP 429; over-limit request rejected | HELD |
| FL01_11 | HTTP 429; over-limit request rejected | HELD |
| FL01_12 | HTTP 429; over-limit request rejected | HELD |

**Ten selected audit log entries**

<!-- Choose entries that show the interesting failures, not the ten easiest. -->

The attack-set run recorded only the two rate-limit rejections for RQ10 and
RQ11 below. Its connection resets and other 400 responses did not produce
audit entries. The other eight records are from the Milestone 1 flood test at
02:07 UTC: three accepted decisions and five rate-limit rejections. These are
verbatim entries from the audit log; rejected requests correctly have fewer
fields than decisions.


```json
[
     {"timestamp":"2026-11-05T02:07:24+00:00","content_id":"4f81cee1-368e-4016-ab94-6e1438245e6e","creator_id":"flood_tester","guess":"human","model_score":0.2587,"style_score":0.3356,"combined_score":0.2895,"label":"We think this was probably written by a person.","status":"decided"},
     {"timestamp":"2026-11-05T02:07:24+00:00","content_id":"46c1f89b-c1bf-4273-a052-afd965ac4564","creator_id":"flood_tester","guess":"human","model_score":0.2587,"style_score":0.3356,"combined_score":0.2895,"label":"We think this was probably written by a person.","status":"decided"},
     {"timestamp":"2026-11-05T02:07:24+00:00","content_id":"152e1614-9384-4400-a1b0-35ed0edc828a","creator_id":"flood_tester","guess":"human","model_score":0.2587,"style_score":0.3356,"combined_score":0.2895,"label":"We think this was probably written by a person.","status":"decided"},
     {"timestamp":"2026-11-05T02:07:24+00:00","creator_id":"flood_tester","event":"rejected","status":"rejected","reason":"rate_limited","limit":"5 per 1 minute"},
     {"timestamp":"2026-11-05T02:07:24+00:00","creator_id":"flood_tester","event":"rejected","status":"rejected","reason":"rate_limited","limit":"5 per 1 minute"},
     {"timestamp":"2026-11-05T02:07:24+00:00","creator_id":"flood_tester","event":"rejected","status":"rejected","reason":"rate_limited","limit":"5 per 1 minute"},
     {"timestamp":"2026-11-05T02:07:24+00:00","creator_id":"flood_tester","event":"rejected","status":"rejected","reason":"rate_limited","limit":"5 per 1 minute"},
     {"timestamp":"2026-11-05T02:07:24+00:00","creator_id":"flood_tester","event":"rejected","status":"rejected","reason":"rate_limited","limit":"5 per 1 minute"},
     {"timestamp":"2026-11-05T13:36:22+00:00","creator_id":"unknown","event":"rejected","status":"rejected","reason":"rate_limited","limit":"5 per 1 minute"},
     {"timestamp":"2026-11-05T13:36:32+00:00","creator_id":"unknown","event":"rejected","status":"rejected","reason":"rate_limited","limit":"5 per 1 minute"}
]
```

**The single worst outcome** — the one I'd least want to explain to a writer
whose work got caught by it:
FP01, a plain and clear human-writing test, got a connection reset instead of
a result. That is the outcome I would least want to explain: the writer gets
neither a decision nor a usable appeal path. The run did not score FP01 or the
other false-positive cases, so it does not establish that the detector falsely
accused them; it shows the service failed before deciding.



---

## Run Log and Verdicts

<!-- Your five criteria across three trials. `run_eval.py --label before`. -->

Report: `results/run_2026-11-05_0951_before.md`, produced by
`run_eval.py::main`.

| Criterion | Target | Trial 1 | Trial 2 | Trial 3 | Overall |
|---|---|---|---|---|---|
| 1. My own writing | At most 1/10 labeled high-confidence AI in every trial | 0/10, MET | 0/10, MET | 0/10, MET | MET |
| 2. AI versus human score spread | Mean AI score at least 0.20 above mean human score in every trial | Gap 0.3833, MET | 500 and connection reset left the comparison incomplete, MISSED | Gap 0.3833, MET | MISSED |
| 3. Label coverage | At least one human, unsure, and AI label in every trial | Human and unsure only, MISSED | Human and unsure only; no AI label, MISSED | Human and unsure only, MISSED | MISSED |
| 4. Appeal round-trip | Five successful appeals, recorded with the original decisions preserved | 5/5, MET | 5/5, MET | Two submissions returned 500 and could not be appealed, MISSED | MISSED |
| 5. Malformed input and health | Required invalid inputs return 4xx, no 5xx, health remains 200 | 4xx; health 200, MET | 4xx; health 200, MET | 4xx; health 200, MET | MET |

**Real output from one trial**, pasted as text, naming the file and function
that produced it:

```json
{
     "report": "results/run_2026-11-05_0951_before.md",
     "producer": "run_eval.py::main",
     "criterion": "AI versus human score spread",
     "trial": 1,
     "clearly_ai_mean": 0.60068,
     "clearly_human_mean": 0.2174,
     "gap": 0.38328,
     "target_gap": 0.20,
     "verdict": "MET"
}
```

**Diagnoses**

<!-- For each miss AND each broken attack: the stage and the mechanism.

     Your service has five stages: the route, signal one, signal two, the
     combining rule, and the label mapping.

     Not a diagnosis:  "The evasion attacks got through."
     A diagnosis:      "Four evasion inputs got through. All four had typos
                        added to AI-generated text. My second signal measures
                        word variety, and typos raise word variety — so it read
                        them as more human. My combining rule weights that
                        signal at 0.6, so it dragged the whole score down."

     Look for a pattern. Five failures on one signal is one problem, not five. -->

Criterion 2 missed overall because Trial 2 did not produce all ten scores: an
AI sample returned HTTP 500 and a later request reset the connection. Stage:
route/inference boundary, before combining. Mechanism: the request failed
before both signal values and a combined score could be returned, so the
five-versus-five comparison is incomplete rather than evidence of a bad
threshold.

Criterion 3 missed in all three trials. Stage: label mapping. Mechanism: the
AI-like samples that were scored reached 0.5898 and 0.6383, both below the
0.65 AI cutoff, so they mapped to `unsure`; the trials produced no high-
confidence AI label.

Criterion 4 missed in Trial 3. Stage: route/inference boundary, before a
`content_id` exists. Mechanism: two submissions returned HTTP 500, so those
requests could not enter the appeal flow. The appeal handler did record
successful appeals and preserve their original decisions.

The 24 evasion, false-positive, and prompt-injection cases, plus MF02, all
ended in connection resets with no scores. Stage: route/inference boundary.
Mechanism: the service closed the connection before returning an HTTP result;
these cases therefore show service failures, not demonstrated detector
bypasses or false accusations.

MF03-MF08 returned scored decisions for control-only, punctuation-only,
single-word, emoji-only, right-to-left, and 60,000-character text. Stage:
route validation and input policy. Mechanism: current validation checks type,
blankness, and a 100,000-character maximum, but does not define whether these
content forms are meaningful or supported.

The flood was held after five accepted requests with 429 responses. The
remaining risk is not this single-process test but the in-memory limiter: a
restart or another worker does not share the same counters.



---

## The Improvement
**What I changed:** The `/submit` path checks that the body is a JSON object,
validates `text` and `creator_id`, rejects blank or over-100,000-character
text before inference, and maps detector `ValueError` and `DetectorUnavailable`
exceptions to JSON 400 and 503 responses. The rate-limit key also handles
non-object JSON safely, and rejected rate-limited requests are written to the
audit log.
**What I changed:**
**Why:** The failures and malformed inputs occur at the route/inference
boundary, before scores or labels exist. Request validation and explicit error
responses keep those cases out of scoring and make rejections observable; they
do not change the detector's thresholds or claim to fix its classification
limits.

**Which diagnosis pointed at it:** The route/inference failures and the
malformed-request cases in the before run. This is request-path hardening, not
a detector improvement.
**Which diagnosis pointed at it:**

### Attack Run — After
No `run_attacks.py --label after` report is present in the workspace, so there
is no verified post-change outcome table. I will not reuse the before results
as after results. Run the full attack set with the `after` label and paste its
56 outcomes here before claiming the improvement held.
<!-- Same format. `run_attacks.py --label after` -->



The code now returns explicit client or service errors for the handled request
and detector exceptions, and the recorded rate-limit tests show 429 responses
and rejection audit entries. The attack/evaluation reports in this workspace
are explicitly labeled `before`; without a post-change full run I cannot claim
that the connection-reset cases were fixed or quantify a change in attack
outcomes.
<!-- Widening the unsure band usually fixes one problem and creates another.
     Reporting that trade honestly is worth full credit. -->



---

## What's Still Broken

<!-- For each attack still getting through and each criterion still missed:
     what you'd do, and why you stopped. -->

The before attack run did not produce scores for EV01-EV10 (evasion), FP01-FP08
(human false-positive cases), or PI01-PI06 (prompt injection): all 24 requests
ended in connection resets. I would first fix and rerun the inference/service
path, then inspect the scores and labels for each family; until that rerun,
these cases are untested, not proven detector bypasses or false accusations.
I stopped because the available run had no classification evidence, and I ran
out of time to get a stable full run.

MF03-MF08 all returned HTTP 200. That includes control-character-only and
punctuation-only text labeled human, plus a long single word, emoji-only text,
right-to-left text, and a 60,000-character submission labeled AI. I would
define and test a minimum meaningful-text policy for control-only and
punctuation-only input, while explicitly deciding what languages and symbol
content the service supports; the current bad-input criterion only covers
missing, null, non-string, blank, and over-limit text. I stopped short of
changing the route because these accepted cases were outside that criterion
and a language policy needs a product decision.

The flood test allowed the first five requests from one creator and returned
429 for later requests, so the configured 5-per-minute limit did stop the
burst. The first five are still accepted by design; for a real deployment I
would add shared, persistent rate-limit storage so separate service workers
cannot each grant a fresh allowance. I did not test multiple workers in this
unit.

Criterion 2, the 0.20 mean score-gap target, is not established across all
three trials: successful samples showed a useful gap, but an AI sample returned
HTTP 500 in one trial, leaving that five-versus-five comparison incomplete. I
would fix the intermittent inference failure and rerun all three complete
trials; I stopped before making a scoring change because the available scores
do not show that the thresholds caused the missing result.

Criterion 3, label coverage, was missed: the calibration set returned human
and unsure, but no high-confidence AI label in the recorded trials. The two
AI-like samples scored 0.5898 and 0.6383, below the 0.65 AI cutoff. I would
collect more labeled examples and validate a threshold adjustment against
human false positives before changing it; I stopped because lowering the cutoff
without that check could turn the known uncertainty into wrong accusations.

Criterion 4, the appeal round-trip, was missed in a trial when two submissions
returned HTTP 500, so they never produced content IDs to appeal. The successful
appeals were recorded correctly and preserved the original decisions. I would
stabilize inference and rerun the full five-appeal trial; I stopped rather than
mistake a failed submission for an appeal-handler defect.

Criteria 1 and 5 passed in the recorded evaluation: the known-human samples
were not labeled high-confidence AI, and missing, null, non-string, blank, and
over-limit requests returned 4xx responses while health stayed at 200.


**The trade I'd make if this ran for real:**

<!-- Two sentences. Fewer wrong accusations means more AI text getting through.
     Say which way you'd go and WHO PAYS FOR IT. -->

I would favor fewer false accusations: keep the high-confidence AI label
conservative and send borderline work to human review, even though more AI text
will pass as human or remain unsure. The site pays through extra review effort
and some missed AI submissions, while writers avoid bearing the larger cost of
being wrongly accused by an unreliable detector.



<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 7

       [ ] criteria.md has five numbered criteria, each naming a target
       [ ] Each has a reason underneath
       [ ] POST /submit returns content_id, guess, confidence, label,
           model_score and style_score
       [ ] Two signals that measure DIFFERENT things, each with a named blind spot
       [ ] Three label variants, all reachable, written out in full
       [ ] POST /appeal changes status and writes to the log
       [ ] Signals and Scoring names scoring.py::combine_signals
       [ ] Sample Run: a submission AND an appeal, as pasted text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN

     SUBMISSION CHECKLIST — unit 8

       [ ] Rate limiting on /submit, with your numbers justified
       [ ] The pasted run of status codes showing 429
       [ ] Audit log with all nine fields, recording rejections too
       [ ] The attack set run IN FULL, every input with an outcome
       [ ] Ten audit log entries pasted as text
       [ ] Five criteria across three trials
       [ ] A diagnosis for every miss and every broken attack — stage AND mechanism
       [ ] One improvement, with Attack Run — After
       [ ] What's Still Broken, including the production trade
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
