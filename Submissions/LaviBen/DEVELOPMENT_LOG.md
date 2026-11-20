# Development log

## 1. Tests before implementation

The shared algorithm and generator tests were written before
`search_algorithms.py` or `synthetic_data.py` existed.

Command:

```bash
python3 -m unittest discover -s tests -v
```

Observed pre-implementation result: exit code `1`, with two import errors:
`No module named 'search_algorithms'` and `No module named 'synthetic_data'`.
This confirms the tests detected the missing behavior instead of passing
without exercising an implementation.

## 2. Version 1 and manual trace

Version 1 implemented manual linear search, recursive binary search over one
sorted copy, and membership using Python's standard-library `set`. The first
complete run passed all seven tests.

Manual trace for IDs `[7, 11, 7]` and queries `[11, 9, 7]`:

- Linear search:
  - `11`: compare with `7`, then `11` -> `True`.
  - `9`: compare with `7`, `11`, and `7` -> `False`.
  - `7`: compare with the first `7` -> `True`.
- Binary search first creates `[7, 7, 11]` without changing the input:
  - `11`: `(low=0, high=2, middle=1, value=7)`, then
    `(low=2, high=2, middle=2, value=11)` -> `True`.
  - `9`: inspect `7`, then `11`; the bounds become `low=2, high=1` ->
    `False`.
  - `7`: the first midpoint value is `7` -> `True`.
- Hash-set membership builds `{7, 11}` and checks the queries in their given
  order -> `[True, False, True]`.

All three methods therefore return `[True, False, True]`, and the original ID
array remains `[7, 11, 7]`.

## 3. Revision

The original public binary search called a recursive helper once per search
step. Version 2 replaces that public implementation with a `while low <= high`
loop. The revision:

- preserves the same sorted-copy and ordered-query contract;
- preserves version 1 as `binary_search_recursive_v1`;
- avoids repeated Python function-call overhead and recursion-stack space; and
- makes the index updates visible in one function, which simplifies tracing.

Review also identified missing boundary coverage. A shared case now searches
below the minimum, at the minimum, within a duplicate run, at the maximum, and
above the maximum. Generator tests were extended to zero queries and 0%/100%
hit rates. No expected result was weakened.

After the revision, all eight core/generator tests passed. Two additional
pipeline tests verify that every implementation is measured and that JSON, CSV,
and HTML artifacts can be regenerated.

In the recorded 10,000-ID benchmark, the iterative median was `1.200667 ms`
versus `1.279875 ms` for the recursive version. That result supports the local
revision decision but is not a proof that every machine or input will show the
same difference.

## 4. AI use

OpenAI Codex assisted with implementation, test design, benchmarking, and
documentation. The human author remains responsible for reviewing the code and
claims.

Accepted suggestions:

- use one shared case table so all search methods face identical tests;
- sort once per binary-search call rather than once per query;
- retain recursive version 1 and make iterative version 2 the public method;
- construct guaranteed misses from a disjoint integer range rather than retry
  random values;
- use a local seeded random generator, `perf_counter_ns`, repeated runs, and a
  median summary; and
- generate a dependency-free dashboard from machine-readable benchmark data.

Corrected suggestions or execution issues:

- `pytest` was initially considered, but it was unavailable in the environment;
  the solution uses standard-library `unittest` with no loss of required
  coverage.
- the first shell wrapper used zsh's reserved variable name `status` after the
  deliberately failing test run; it was changed to `test_exit`, and the
  pre-implementation run was repeated to record exit code `1` cleanly.
- boundary and extreme-hit-rate cases were added after reviewing the first
  passing suite.

Rejected suggestions:

- using `bisect` or `list.index`, because both search procedures must be
  implemented directly;
- sorting the caller's list in place, because the input must remain unchanged;
- timing synthetic-data generation, because the assignment requires generation
  to remain separate from algorithm measurement; and
- adding NumPy, pandas, or a charting package, because the standard library is
  sufficient and keeps the submission easier to reproduce.

## 5. Fixed-input benchmark revision

New benchmark tests were written before the measurement refactor. The baseline
run exited with code `1`: `SCENARIOS` did not exist in the old benchmark, and a
single 50% query used floor rounding and became absent. This confirmed the new
tests rejected the previous design.

The revised benchmark now:

- generates every `(n, q, scenario)` case once before timing;
- converts IDs and queries to immutable tuples and stores an input SHA-256;
- gives all methods and both binary versions the identical tuple objects;
- separates preparation from the complete query batch and directly brackets
  their combined elapsed time;
- includes sorting and set construction in preparation;
- rotates algorithm order between repeats to reduce fixed-order bias;
- saves every raw repetition plus median summaries;
- records units, seeds, requested and realized hit rates, duplicate policy,
  generator version, Python/machine details, Git commit, and source hash; and
- records why a one-query mixed case realizes either zero or one hit (the
  selected nearest-integer half-up policy realizes one).

One dashboard integration test then exposed an assumption that `q=100` was
always present. The dashboard was corrected to select the largest available
query count, allowing reduced test matrices without changing full-run behavior.
The expanded final suite contains eleven passing tests.

The versioned full run used code commit `b122ea5` with a clean submission tree.
It produced 18 input cases, 360 raw observations, and 72 median summaries. For
`n=100,000`, `q=100`, mixed queries, combined medians were `51.227500 ms`
(linear), `10.596250 ms` (recursive binary), `10.673750 ms` (iterative binary),
and `1.882083 ms` (hash set). The iterative binary query batch itself was
faster than the recursive batch (`0.104333 ms` versus `0.127834 ms`), while
sorting dominated both methods' combined time in this run.

## 6. Memory measurement revision

Memory-evidence tests were added before implementation. The baseline exited
with code `1` because `BenchmarkRun` had no `memory_results` and no memory CSV
artifact existed.

The revision adds a separate memory phase after runtime timing. Every
case/method starts a fresh `tracemalloc` session after the input has already
been built. Preparation and the complete query batch run inside tracing. The
prepared value and returned result remain referenced when current and peak
traced bytes are read, after which tracing stops. This means:

- input IDs and query tuples are excluded;
- the output list is included;
- binary sorted copies and the hash set are included;
- linear search has no allocated preparation structure; and
- temporary Python allocations may be present in the peak.

RSS sampling was rejected for this submission because it is optional, adds a
dependency or platform-specific code, includes interpreter/process overhead,
and can miss brief peaks. The documentation explicitly avoids treating
`tracemalloc` peak bytes as a direct measurement of algorithmic auxiliary
space.

The versioned memory run used clean submission code commit `d4fd34f` and saved
72 fresh tracing results. For `n=100,000`, `q=100`, mixed queries, peak traced
bytes were `864` (linear), `1,199,824` (recursive binary), `1,199,824`
(iterative binary), and `2,621,656` (hash set). The input is excluded from all
four values; preparation and the returned output are included.

## 7. Saved-results dashboard revision

Interactive-dashboard tests were added first. The old static dashboard failed
the new contract because it had no query/scenario controls, saved-data client,
raw-repeat access, or environment-details view.

The revised `dashboard.py` imports only `argparse`, `json`, and `pathlib`. It
reads the previously saved JSON and embeds it in a self-contained HTML file.
Browser JavaScript filters that data without invoking Python. Three charts show
preparation, complete query batch, and total time against input length, with one
curve per method. Additional views compare recursive v1 with iterative v2,
display selected memory rows, expose raw repetitions with CSV download, and
show environment and code metadata.

The generated JavaScript passed `node --check`. No benchmark was rerun while
building or validating this dashboard revision.

## 8. Iterative-loop performance review

The iterative binary-search query loop was reviewed again after the complete
measurement pipeline was in place. Candidate revisions were timed on the same
seeded arrays and ordered query batches for all-present, all-absent, and mixed
queries at `n = 1,000`, `10,000`, and `100,000`.

The accepted revision:

- computes the unchanged last valid index once per batch instead of once per
  query;
- uses `(low + high) // 2`, which is safe because Python integers do not
  overflow; and
- orders the less-than and greater-than branches before the equality case,
  reducing comparisons on many unsuccessful search steps.

In a focused 100-query mixed-case check, the accepted loop reduced median query
time by about 14--16% at the three tested input lengths. The subsequent full
18-case validation made its `q=100` query batch faster in all nine
size/scenario combinations; the median reduction relative to the saved run was
`12.8%`. A lower-bound-style loop was rejected even though it was fastest for
all-absent queries: it was slower for all-present queries and was not the best
balanced choice across the three required scenarios. A `for`/`else`
linear-search rewrite was also rejected because it was neutral or slower in
most measurements. The hash-set list comprehension, `set(ids)`, and
`sorted(ids)` were retained because they already delegate their permitted
operations to optimized standard-library code.

These measurements support a local implementation decision; they do not prove
that one search strategy is universally fastest on every machine or workload.
