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

```

---

## Attack Run — Before

<!-- Every attack with its outcome and a held-or-broke mark.
     `run_attacks.py --label before` produces the table. -->



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

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |
| 2.  |  |  |  |  |  |
| 3.  |  |  |  |  |  |
| 4.  |  |  |  |  |  |
| 5.  |  |  |  |  |  |

**Real output from one trial**, pasted as text, naming the file and function
that produced it:

```json

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



---

## The Improvement

**What I changed:**

**Which diagnosis pointed at it:**

### Attack Run — After

<!-- Same format. `run_attacks.py --label after` -->



**Did it help, and how do I know:**

<!-- Widening the unsure band usually fixes one problem and creates another.
     Reporting that trade honestly is worth full credit. -->



---

## What's Still Broken

<!-- For each attack still getting through and each criterion still missed:
     what you'd do, and why you stopped. -->



**The trade I'd make if this ran for real:**

<!-- Two sentences. Fewer wrong accusations means more AI text getting through.
     Say which way you'd go and WHO PAYS FOR IT. -->



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
