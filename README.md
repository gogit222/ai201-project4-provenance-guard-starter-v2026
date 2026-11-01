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

Calibration readings (model score / style score):

| Input | Model | Style |
|---|---:|---:|
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
| high-confidence human |  |  |
| unsure |  |  |
| high-confidence AI |  |  |

**Why I worded the "unsure" one this way:**
<!-- It's the hardest of the three. It has to admit uncertainty without
     sounding like an accusation, because the person reading it may well have
     written every word themselves. -->



---

## Sample Run

<!-- One submission and one appeal, pasted as text: the request, the response,
     and the log entries. -->

**A submission**

This sample was tested on a temporary non-debug server at port 5001. The
existing debug server on port 5000 reset the connection when the first model
inference ran.

```powershell
$body = '{"text":"The implementation of this system requires careful consideration of several important factors. First, the service should validate incoming data to ensure reliable processing. Additionally, each stage should provide consistent results and maintain clear records. By following these principles, the system can deliver an effective and user-friendly experience.","creator_id":"milestone4_curl"}'
$body | curl.exe -i -X POST http://127.0.0.1:5001/submit -H "Content-Type: application/json" --data-binary '@-'
```

```json
{"combined_score":0.6102,"confidence":0.6102,"content_id":"adf3f7f0-5877-4c65-9518-e0956b75739b","guess":"ai","label":"Pending combined scoring and final label mapping.","model_score":0.6771,"style_score":0.5098}
```

**The audit log after submission**

```powershell
curl.exe -i "http://127.0.0.1:5001/log?limit=1"
```

```json
{"count":1,"entries":[{"combined_score":0.6102,"content_id":"adf3f7f0-5877-4c65-9518-e0956b75739b","creator_id":"milestone4_curl","guess":"ai","label":null,"model_score":0.6771,"status":"decided","style_score":0.5098,"timestamp":"2026-11-01T13:00:07+00:00"}]}
```

**An appeal**

```bash
$ curl -X POST http://127.0.0.1:5000/appeal \
  -H "Content-Type: application/json" \
  -d '{"content_id": "...", "reasoning": "..."}'
```

```json

```

**What the log shows afterwards**

```bash
$ curl "http://127.0.0.1:5000/log?limit=3"
```

```json

```

---

## How I Used AI

**Moment 1**

- *What I asked for:*
- *What came back:*
- *What I changed:*

**Moment 2**

- *What I asked for:*
- *What came back:*
- *What I changed:*

<!-- ═══════════════════════ UNIT 8 — THE TEST ═══════════════════════ -->

---

## Rate Limiting

**My limits:** ___ per minute, ___ per day

**Why those numbers and not others:**
<!-- Think about two people: a real writer submitting their own work a few
     times an hour, and a script sending a thousand variations to map your
     thresholds. Your numbers have to be liveable for the first and hostile to
     the second. -->

**What a caller counts as:** <!-- per address, or per creator_id? They fail
differently — one script can look like a thousand callers, and one household
can look like one. -->

**The run of status codes when I pushed past it:**

<!-- python run_attacks.py --flood 15 -->

```

```

---

## Attack Run — Before

<!-- Every attack with its outcome and a held-or-broke mark.
     `run_attacks.py --label before` produces the table. -->



**Ten audit log entries from the run**

<!-- Choose entries that show the interesting failures, not the ten easiest. -->

```json

```

**The single worst outcome** — the one I'd least want to explain to a writer
whose work got caught by it:



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
