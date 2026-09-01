# Evaluation

## Why this exists

The v2.6.0 changelog claimed **"96-97% accuracy maintained"** after migrating
from `llama-3-3-70b-instruct` to `mistral-small-3-1-24b-instruct-2503`.

Nothing substantiated it. No suite existed, no number had been produced, and
the figure had been sitting in the changelog being repeated. This measures it.

## How accuracy is measured

By **execution**, not string comparison. The reference query and the generated
query both run against the same database and their result sets are compared.

This matters more than it sounds. Two different SQL statements can be equally
correct, and grading on text would fail perfectly good queries for choosing a
different join order or a different way of expressing a date filter. The
question is whether the user got the right answer.

Two levels are reported:

| Metric | Meaning |
|---|---|
| **Execution accuracy** | The result sets are identical. This is the headline number |
| Value accuracy | Every value in the reference result appears in the generated result. Catches "right numbers, extra columns" |
| Valid SQL rate | The generated query executed at all |
| Routing accuracy | The classifier sent the question down the right path |

Routing is graded separately because a greeting sent to the SQL generator
wastes a model call and produces nonsense, and that failure is invisible in a
SQL-only score.

The suite is 33 cases across six categories: aggregates, ranking, filtering,
existence checks, listing, and conversational routing.

## Results

All runs use the same 33 cases and the same generated dataset.

| Run | Model | Prompts | Execution accuracy | Routing | Valid SQL | Median latency |
|---|---|---|---|---|---|---|
| Baseline | `llama-3-3-70b-instruct` | v2 | 92.9% | 100% | 100% | 7.25s |
| Baseline | `mistral-small-3-1-24b` | v2 | 89.3% | 100% | 100% | 0.83s |
| **Current** | **`mistral-small-3-1-24b`** | **v3** | **100%** | **100%** | **100%** | **0.50s** |

### What this says about the v2.6.0 claim

**The claim was wrong.** Neither model scored 96-97% on this suite under the
prompts that shipped with that release.

What actually happened at v2.6.0 was a **trade, not a free win**: the migration
cost **3.6 percentage points of execution accuracy** and bought roughly **8.7x
lower latency**. That is a defensible decision for an interactive demo, where
seven seconds per question is its own kind of failure. It is just not the
decision the changelog describes, and "maintained" was the wrong word.

The trade was made explicitly on 2026-09-01: **keep the faster model**. The
accuracy gap has since been closed by other means.

### What closed the gap

Not a bigger model - better prompts. The failures had a single root cause worth
stating plainly:

> The prompt described the **columns** but never the **values inside them**.

The model could not know that `document_type` contains `'Credit'`, or that
`multi_year_deal_flag_so` is `'Yes'` rather than `'Y'`. It was guessing, and
guessing plausibly, which is the worst kind of wrong.

| Failing case | Baseline behaviour | Fix |
|---|---|---|
| `credit-total` | Searched `item_description LIKE '%credit%'` | Documented `document_type` values |
| `multi-year-deals` | Guessed `'Y'`; both models did | Documented the flag values |
| `revenue-for-named-customer` | Filtered `end_user_company_name` | Rule: an unqualified company name means `customer_name` |
| `top-3-end-users` | Failed on llama only | Fixed by the same changes |

Adding a `COLUMN VALUES` section and one disambiguation rule took the faster,
smaller, cheaper model from 89.3% to 100% - past the larger model it replaced.

## Honesty about the 100%

**100% on 33 cases is not "100% accurate".** It means the suite has stopped
finding faults, which is a weaker statement and a normal place to be.

Three caveats belong with that number:

1. **The suite is small**, and every case was written by the same person who
   then fixed the failures. An eval you tune against gradually becomes a
   training set. The honest reading is "no known failures", not "no failures".
2. **The dataset is synthetic and fixed.** Real data has nulls in awkward
   places, inconsistent spellings and duplicate entities. None of that is here.
3. **The questions are well-formed.** Real users ask ambiguous, truncated and
   contradictory questions. Only one case in this suite is deliberately
   ambiguous.

The right next step is not celebrating the number, it is adding cases that
break it.

## An episode worth recording

Moving the prompts out of Python and into files looked like a pure refactor.
The suite went from **89.3% to 10.7%**, with almost every case reporting "no
SQL produced".

The cause was one character. The prompt loader called `.strip()`, which removed
the trailing newline after the user's question - the newline that tells the
model to start a new line, with SQL on it. Without it the model carried on
writing the question.

**All 101 unit tests passed throughout.** Nothing about the application was
broken in a way that any test could see; the prompt was still a string, the
route still returned 200, and the answer was still well-formed prose. Only an
eval that ran real questions against a real model could catch it.

That is the argument for having them.

## Running the suite

```bash
python evals/run_evals.py                                    # current model
python evals/run_evals.py --model meta-llama/llama-3-3-70b-instruct
python evals/run_evals.py --output evals/results/run.json    # full record
python evals/run_evals.py --only credit-total                # one case
```

Requires `IBM_API_KEY` and `PROJECT_ID`, and a built dataset (`python
scripts/generate_dataset.py`). Set `DEMO_DAILY_QUESTION_LIMIT=0` to run
unmetered.

The suite is **not** wired into CI. It costs real model calls on every run and
needs live credentials, which is the wrong thing to put on every pull request.
It is run deliberately, before and after any change to a prompt or a model, and
the results are recorded here.

## Cost per run

Measured against the live prompts:

| Prompt | Input tokens |
|---|---|
| Classifier | 228 |
| SQL generator | 2,013 |
| Conversational | 302 |

A data question costs roughly **2,300 tokens**, almost all of it the SQL
generator's few-shot examples. A full 33-case run is therefore around 60,000
tokens.

That concentration is worth noting: **the few-shot examples are about 88% of
the cost of every question asked.** Trimming them is the obvious optimisation
if cost ever matters, and the suite is what would make it safe to try.
