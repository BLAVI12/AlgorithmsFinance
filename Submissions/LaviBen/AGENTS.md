# LaviBen submission rules

These instructions apply to all work under `Submissions/LaviBen/`.

## Repository and Git scope

- Work on a topic branch in Ben Lavi's `BLAVI12/AlgorithmsFinance` fork.
- Never commit or push to `main` or to the `cogeorg` upstream remote.
- Do not edit course folders or another student's submission. Phase 2 evidence
  belongs under `phase2_<student>/` and must inspect an exact detached commit.
- Preserve unrelated working-tree changes. Stage only `Submissions/LaviBen/`
  paths that belong to the current task.
- Commit or push only when requested. AI-assisted commits must include
  `Co-Authored-By: OpenAI Codex <codex@openai.com>`.

## Tests and correctness

- Add a failing regression test before fixing a reproduced bug. Run it once to
  prove that it detects the old behavior, then run the complete suite.
- Never weaken a valid expected result or hide a measurement contradiction.
- All implementations must use the same contract cases, preserve input and
  query order, and return one real `bool` per query.
- Keep synthetic-data generation, algorithms, runtime measurement, and the
  saved-results dashboard separate.

## Benchmark integrity

- Generate each `(n, q, scenario)` input once and give every method/version the
  identical immutable objects and input digest.
- Reject duplicate sizes, query counts, and scenarios. Case IDs must be unique
  and include their seed; summaries must also match the input digest.
- Isolate each algorithm in a helper. Release prepared states and outputs and
  run cyclic collection outside every timing window so cleanup is never charged
  to the next method.
- Batch short operations, divide elapsed time by the saved call count, and
  record clock implementation, resolution, observed overhead, target window,
  and cap. Report timer overhead; do not silently subtract it.
- Preparation, query-batch, and combined values are independent estimates.
  Combined must bracket both operations in its own run, but must not be clamped
  to or presented as the arithmetic sum of the other samples.
- Use seeded signed, duplicate-heavy IDs. When representable, absent queries
  must cover below-minimum, internal-gap, and above-maximum values.

## Memory and dashboard evidence

- Build inputs first, collect garbage, then start a fresh `tracemalloc` session
  for every case/method. Read current and peak bytes while the prepared state
  and returned output remain alive. State explicitly that input is excluded,
  preparation/output are included, and native allocations may be omitted.
- The dashboard must load saved results only. It must expose requested and
  realized hit rates, units, preparation/query/total views, memory, raw repeats,
  environment, clock data, and batch call counts.
- Plot numeric input length on a logarithmic x-axis. Use distinct dash patterns
  and marker sizes so overlapping algorithm versions remain visible.
- Do not claim one method is universally fastest. Describe the measured
  workload and the time/memory trade-off.

## Versioned artifacts and completion checks

- Commit measurement code before the canonical benchmark. Run the benchmark
  from a clean submission tree so saved metadata records the actual code commit
  and `submission_tree_dirty` is false.
- After a canonical run, rebuild the dashboard from JSON, verify it is
  byte-stable, verify raw-to-summary medians and memory invariants, and validate
  the embedded JavaScript syntax.
- The default full run must produce 18 cases, 360 raw timing rows, 72 summaries,
  and 72 memory rows unless the documented matrix or repeat count intentionally
  changes.
- Before handoff, run:

  ```bash
  cd Submissions/LaviBen
  python3 -m unittest discover -s tests -v
  python3 -m compileall -q .
  python3 dashboard.py
  ```

- Record an immutable audit commit and annotated tag only after the complete
  project and saved artifacts pass verification. Resolve and copy the full SHA
  with `git rev-parse`; never type or guess it from a short SHA.
