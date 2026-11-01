# Acceptance criteria — Provenance Guard

Five criteria that say what "working" means for this service, written in unit 7
**before** you built it.

**All five are yours.** None are given.

An acceptance criterion names a number or something plainly observable. *"The
detector is accurate"* is an opinion — and perfect AI detection isn't possible
anyway, so it's an opinion about something nobody can deliver. *"Of 10 pieces I
wrote myself, at most 1 is labelled high-confidence AI"* is a criterion.

Under each, write a sentence or two on **why that target**. *"I allow at most 1
false positive in 10 because on a writing site a wrong accusation costs more
than a missed detection"* is a real answer.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

---

## Pick numbers you can defend

**Cover at least three of these five areas.** They're prompts, not a form.

| Area | A question it could answer |
|---|---|
| False positives | How often may a human's writing get called AI? |
| Score spread | How far apart should clearly-AI and clearly-human text score? |
| Label coverage | Is every one of your three labels actually reachable? |
| The appeal path | Does an appeal always change status and always get recorded? |
| Bad input | What happens when `text` is missing, empty, or enormous? |

Two things worth knowing before you pick numbers:

- **The expensive mistake is one-sided.** Missing some AI text costs the site a
  little. Accusing a real writer costs that person a lot. A criterion that
  treats both errors as equally bad is describing a system nobody would ship.
- **Unit 8 tests across three trials, and the target has to hold across all
  three.** Your first signal runs a model, so identical input can score
  differently twice. A target of "at most 1 in 10" against trials of 2, 1, 2 is
  a **miss**.

---
## 1.

For each of three trials, no more than 1 of 10 pieces of my own human-written text is labelled high-confidence AI.



**Why this target:**
A false accusation can harm a writer more than a missed AI-generated passage harms the site, so the high-confidence AI label should be rare on work I know is mine. Requiring the limit in every trial prevents a good average from hiding an inconsistent run.



---

## 2.

In each of three trials, the mean combined score for 5 clearly AI-written samples is at least 0.20 higher than the mean combined score for 5 clearly human-written samples.



**Why this target:**
A measurable gap shows the combined score distinguishes the two calibration groups, while a 0.20 margin is large enough to be useful rather than a tiny difference lost in model variation.



---

## 3.

Across three trials on the same 5 calibration samples, the service returns at least one `human`, one `unsure`, and one `ai` label in every trial.



**Why this target:**
All three labels need to be reachable for the unsure band to serve as a real alternative to an accusation, not just an unused code path. Repeating the same samples checks that model variation does not make a label disappear.



---

## 4.

For 5 appeals against existing submissions, every request returns HTTP 200 and adds an audit entry for the same `content_id` with `event: "appeal"` and `status: "under_review"`; each original decision remains in the log.



**Why this target:**
A writer needs a reliable way to challenge a wrong result, and an append-only record preserves both the original decision and the review request for later follow-up.



---

## 5.

Missing, null, non-string, or blank `text` values return a JSON 4xx response. Text longer than 100,000 characters returns a JSON 4xx response. None of these requests returns 5xx, and `GET /health` still returns HTTP 200 afterward.



**Why this target:**
Invalid input should be rejected clearly before it reaches the model, while a documented size limit prevents oversized submissions from consuming unbounded resources. Keeping the service healthy after these requests guards against malformed input crashing the route or process.



---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 8 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath, like this:

         ## 2. Uncertain cases land in the unsure band

         The system handles uncertain cases well.

         **Why this target:** ...

         > **Revised in unit 8:** Text I judged borderline scores between
         > 0.4 and 0.6 in at least 4 of 5 cases.
         >
         > **Why revised:** "well" gave me nothing to check. I couldn't
         > reach a verdict from it at all.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "At most 1 of 10 of my own pieces flagged as AI" → "at most 3
            of 10", because 1 of 10 turned out to be hard.

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->
