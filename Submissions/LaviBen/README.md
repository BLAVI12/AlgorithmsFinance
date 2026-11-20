# Search Algorithms — LaviBen

- **Student:** Ben Lavi
- **Required folder name:** `LastnameFirstname` -> `LaviBen`
- **Language:** Python 3.10+

Tests-first implementation and runtime comparison of three ways to answer
ordered membership queries over integer IDs:

1. manual linear search;
2. manual binary search over a sorted copy; and
3. Python standard-library hash-set membership.

All methods return one Boolean per query in the original query order and leave
the supplied ID array unchanged. The recursive binary-search version is kept
beside the revised iterative version for direct comparison.

## Quick start

Python 3.10 or newer is sufficient; there are no third-party dependencies.
The recorded environment uses CPython 3.14.7 (`.python-version`), and
`requirements.txt` explicitly records the absence of third-party packages.

```bash
cd Submissions/LaviBen
python3 -m unittest discover -s tests -v
python3 benchmark.py
python3 dashboard.py
```

Open `results/runtime_dashboard.html` in a browser to inspect the generated
dashboard.

`dashboard.py` reads `results/benchmark_results.json` only. It does not import
or call the benchmark or search modules, so regenerating the dashboard and
changing its browser controls cannot rerun measurements.

## Example

```python
from search_algorithms import binary_search, hash_set_membership, linear_search

ids = [7, 11, 7]
queries = [11, 9, 7]
expected = [True, False, True]

assert linear_search(ids, queries) == expected
assert binary_search(ids, queries) == expected
assert hash_set_membership(ids, queries) == expected
assert ids == [7, 11, 7]
```

## Implementations

| Function | Approach | Total time for `n` IDs and `q` queries | Extra working space* |
|---|---|---:|---:|
| `linear_search` | Scan IDs for each query | `O(nq)` | `O(1)` |
| `binary_search_recursive_v1` | Sort once, recursively halve each search range | `O(n log n + q log n)` | `O(n + log n)` |
| `binary_search` | Sort once, iteratively halve each search range | `O(n log n + q log n)` | `O(n)` |
| `hash_set_membership` | Build a set once, then perform membership lookups | Expected `O(n + q)` | `O(n)` |

\*Excluding the required `O(q)` result list. Hash-table lookup is expected
`O(1)` per query; adversarial collisions can make the worst case slower.

`sorted(ids)` creates the binary-search copy, so the caller's array is never
sorted in place. Linear and binary search procedures are implemented directly;
the core does not delegate to `list.index`, `bisect`, or another search helper.

## Tests-first evidence

The tests were created before either implementation module. The first run
exited with code `1` because `search_algorithms` and `synthetic_data` were
missing. Version 1 then passed all seven original tests. After review, boundary,
generator, fixed-input benchmark, lifetime-isolation, clock-resolution, and
memory-scope cases were added; the final suite contains sixteen passing tests.

The shared cases cover:

- empty arrays and empty queries;
- one present or absent entry;
- duplicates and unsorted inputs;
- negative IDs, repeated queries, and boundary misses;
- present and absent queries in a deliberately mixed order;
- exact Boolean output order and type; and
- unchanged list and tuple inputs.

See [`DEVELOPMENT_LOG.md`](DEVELOPMENT_LOG.md) for the failing baseline, manual
trace, revision record, and AI-use disclosure. See
[`SUBMISSION_CHECKLIST.md`](SUBMISSION_CHECKLIST.md) for the complete
requirement-to-evidence mapping and correctness arguments. Passing tests provide
evidence of expected behavior, not a proof of correctness.

## Synthetic data and measurement

`synthetic_data.py` uses a local seeded random generator and is independent of
both the algorithms and measurement code. IDs are sampled with replacement
from a signed, even-valued pool of `max(1, n // 3)` values, so larger arrays
intentionally contain duplicates. Absent queries are a seeded mixture below
the observed minimum, inside observed gaps, and above the observed maximum.

The benchmark fixes an 18-case matrix before timing:

- array entries `n in {1,000, 10,000, 100,000}`;
- query counts `q in {1, 100}`; and
- `all_present`, `all_absent`, and `mixed` query scenarios.

Each case is generated exactly once, converted to immutable tuples, and
fingerprinted with SHA-256. Every method and version receives that same object
pair. For `q=1`, a literal 50/50 mix is impossible; nearest-integer half-up
rounding produces one present query, and both the requested (`0.5`) and realized
(`1.0`) rates are saved.

Five repetitions rotate method order deterministically. Very short operations
are adaptively batched toward a 2 ms timing window (capped at 10,000 calls).
Every raw row saves the number of calls and elapsed nanoseconds per call. The
timer implementation, resolution, and measured timer-call overhead are saved;
overhead is reported but not subtracted. Prepared states and outputs stay alive
until each timing window closes, then are released and collected before the
next method starts. The benchmark records:

- **preparation:** no index for linear search, sorting for binary search, and
  set construction for hash membership;
- **query batch:** the complete ordered query list; and
- **combined:** elapsed time spanning preparation and the complete batch.

These are three independent batched estimates. Combined time brackets both
operations in its own invocation, but is not calculated as the sum of the
separately sampled preparation and query values; ordinary run-to-run variation
can therefore make a total estimate slightly lower than one component estimate.

Raw nanoseconds-per-call timings and call counts, millisecond medians, seeds,
generator settings, input digests, Python and machine details, and Git/source
versions are saved under `results/`. `dashboard.py` turns the JSON into a
self-contained HTML dashboard without external JavaScript or plotting
libraries. Timings describe one machine and run; rerun the benchmark before
making environment-independent performance claims.

Recorded medians for `n=100,000`, `q=100`, mixed queries:

| Implementation | Preparation (ms) | Query batch (ms) | Combined (ms) |
|---|---:|---:|---:|
| Linear search | 0.000028 | 52.265750 | 52.733458 |
| Binary search recursive v1 | 10.539209 | 0.123992 | 10.618542 |
| Binary search iterative v2 | 10.441750 | 0.086023 | 10.514750 |
| Hash set membership | 1.311521 | 0.001638 | 1.247062 |

This run used Python `3.14.7` on `arm64` and clean submission code commit
`050bfc8`. The recorded clock resolution is `41.667 ns`, median timer-call
overhead is `42 ns`, and q=1 hash query batches contain 586--3,425 calls.
Full machine fields, source SHA-256, batch counts, and raw observations are in
`results/benchmark_results.json`.

### Performance interpretation

No one method is fastest and smallest for every workload. In the recorded
large repeated-query case, hash-set membership has the lowest combined time
because its one-time construction cost is repaid by constant-expected-time
lookups. Linear search has the smallest measured auxiliary allocation and can
be competitive when there is only one query, because it performs no index
preparation. Binary search lies between those trade-offs and becomes more
attractive when its sorted copy can serve many queries.

The preserved versions are useful implementation comparisons, not a controlled
single-factor experiment. Iterative v2 simultaneously removes recursive calls,
inlines the search loop into the batch, caches the last index, changes the
midpoint expression, and reorders comparisons. Its measured difference from
v1 therefore belongs to that complete change set; it cannot be attributed only
to removing recursion. See `DEVELOPMENT_LOG.md` for the accepted and rejected
alternatives. Machine timings support local conclusions but do not prove
universal dominance.

### Interactive dashboard

The self-contained HTML dashboard embeds the saved JSON once and performs all
view changes in browser JavaScript. It provides:

- query-count and present/absent/mixed scenario controls;
- requested and realized hit rates plus timing and memory units;
- separate logarithmic input-length curves for preparation, complete query
  batch, and total elapsed time, with one curve per method and distinct dash
  patterns/marker sizes so overlapping binary versions remain visible;
- a direct recursive-v1 versus iterative-v2 comparison table;
- the chosen current/peak traced-memory rows;
- expandable raw timing repetitions and a filtered CSV download; and
- expandable Python, machine, generator, memory-scope, and code-version
  details.

Run only `python3 dashboard.py` to rebuild the view from existing measurements.
Run `python3 benchmark.py` separately only when intentionally collecting a new
measurement set.

## Reviewer reproduction

The exact immutable review commit is recorded in
[`AUDIT_COMMIT.md`](AUDIT_COMMIT.md). Follow
[`REPRODUCIBILITY.md`](REPRODUCIBILITY.md) to verify that commit without
editing it. The short verification path is:

```bash
cd Submissions/LaviBen
python3 -m unittest discover -s tests -v
python3 -m compileall -q .
python3 dashboard.py
git diff --exit-code -- results/runtime_dashboard.html
```

Expected result: 16 tests pass, compilation succeeds, and the dashboard rebuilt
from saved measurements is byte-for-byte unchanged. `benchmark.py` is a
separate, explicit command because it intentionally records new
machine-specific observations.

Docker packaging was optional and was not selected, so this submission does
not include a `Dockerfile`.

### Memory measurement

Memory is measured in a separate run so `tracemalloc` does not perturb runtime
timings. For every fixed case and method:

1. the input IDs and queries already exist;
2. cyclic garbage is collected, then a fresh `tracemalloc` session starts;
3. preparation and the complete query batch run;
4. the prepared structure and returned output remain alive;
5. `get_traced_memory()` records current and peak traced bytes; and
6. tracing stops before the next method.

Therefore, the original input is **excluded**, while the output is **included**.
Preparation is included: binary-search sorted copies and hash sets are counted;
linear search creates no separate prepared index. Temporary Python allocations
during preparation and querying can affect the peak.

`tracemalloc` does not capture every native allocation, and traced bytes are not
the same as formal auxiliary-space complexity. RSS is not recorded: it would
include the Python interpreter and unrelated process overhead, and periodic
sampling could miss brief peaks. Memory results are stored in bytes in
`results/memory_results.csv` and in the complete JSON evidence.

Recorded traced memory for `n=100,000`, `q=100`, mixed queries:

| Implementation | Current traced bytes | Peak traced bytes | Peak KiB |
|---|---:|---:|---:|
| Linear search | 1,016 | 1,016 | 0.99 |
| Binary search recursive v1 | 802,216 | 1,199,952 | 1,171.83 |
| Binary search iterative v2 | 801,288 | 1,199,952 | 1,171.83 |
| Hash set membership | 2,098,336 | 2,621,704 | 2,560.26 |

These figures exclude the prebuilt 100,000-entry input and query tuple. They
include the returned 100-Boolean output and, where applicable, the sorted copy
or hash set.

## Project layout

| Path | Purpose |
|---|---|
| `search_algorithms.py` | Required methods and preserved recursive version |
| `synthetic_data.py` | Deterministic input generation |
| `benchmark.py` | Fixed-input preparation/query/combined measurement |
| `dashboard.py` | Interactive HTML app generated from saved JSON only |
| `.python-version` | Recorded CPython version (`3.14.7`) |
| `requirements.txt` | Explicit zero-third-party dependency manifest |
| `REPRODUCIBILITY.md` | Exact reviewer and remeasurement commands |
| `AUDIT_COMMIT.md` | Immutable commit selected for audit |
| `tests/` | Shared algorithm, generator, and pipeline tests |
| `results/benchmark_results.json` | Metadata, cases, raw timings, and summaries |
| `results/benchmark_results.csv` | Median preparation/query/combined summary |
| `results/raw_timings.csv` | Every repetition, batch call counts, and ns/call |
| `results/memory_results.csv` | Fresh-run current and peak traced bytes |
| `results/input_manifest.json` | Seeds, hit rates, duplicate policy, and input digests |
| `results/runtime_dashboard.html` | Generated runtime dashboard |
| `DEVELOPMENT_LOG.md` | Test-first, trace, revision, and AI-use evidence |
| `SUBMISSION_CHECKLIST.md` | Requirement mapping and correctness reasoning |

## Phase 2 — Audit

The independent audit of Yannick Welscher's submission is under
`phase2_welscher_yannick/`. It records the exact audited commit, separates
reproduced defects from suspected weaknesses, and includes an executable
reproducer plus detached-worktree instructions.
