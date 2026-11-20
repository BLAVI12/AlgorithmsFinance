# Reproducibility runbook

This submission uses only the Python standard library. The tested interpreter
is CPython `3.14.7`, recorded in `.python-version`; Python `3.10+` is supported.
`requirements.txt` intentionally contains no installable packages.

The immutable commit selected for review is recorded in `AUDIT_COMMIT.md` on
the submission branch. Review that exact commit without editing its files.

## Verify the saved project

From the repository root after checking out the recorded audit commit:

```bash
cd Submissions/LaviBen
python3 --version
python3 -m unittest discover -s tests -v
python3 -m compileall -q .
python3 dashboard.py
```

Expected results:

- Python reports `3.14.7` for the recorded environment; another Python 3.10+
  interpreter may also be used.
- `Ran 11 tests` and `OK`.
- compilation exits successfully without output;
- dashboard generation reports that it wrote
  `results/runtime_dashboard.html` from saved results only; and
- regenerating the dashboard does not modify the tracked HTML file.

Open `results/runtime_dashboard.html` directly in a browser. Its controls use
embedded saved data and do not run measurements.

## Inspect saved evidence

```bash
python3 - <<'PY'
import json
from pathlib import Path

data = json.loads(Path("results/benchmark_results.json").read_text())
print("cases", len(data["cases"]))
print("raw timings", len(data["raw_results"]))
print("summaries", len(data["summary"]))
print("memory rows", len(data["memory_results"]))
print("units", data["metadata"]["units"])
print("measurement code", data["metadata"]["code_version"])
PY
```

Expected counts are 18 cases, 360 raw timings, 72 summaries, and 72 memory
rows. Raw time uses nanoseconds, summary time uses milliseconds, and traced
memory uses bytes.

## Intentionally collect new measurements

Only run this when new machine-specific observations are desired:

```bash
python3 benchmark.py
python3 dashboard.py
```

`benchmark.py` replaces the generated files in `results/`. Runtime values are
expected to vary by machine and load; correctness results and case structure
must remain stable. To preserve the committed evidence, direct a trial run to a
different directory:

```bash
python3 benchmark.py --output /tmp/laviben-benchmark
python3 dashboard.py \
  --input /tmp/laviben-benchmark/benchmark_results.json \
  --output /tmp/laviben-benchmark/runtime_dashboard.html
```

## Measurement definitions

- Inputs are generated once before measurement and shared by every method.
- Preparation includes sorting or set construction; linear preparation retains
  the input reference and creates no index.
- Query-batch time covers the complete ordered query list.
- Combined time directly brackets preparation and the complete query batch.
- A fresh `tracemalloc` run starts after input construction for each method.
  Input is excluded; preparation, prepared structures, and output are included.
- The returned output stays alive when current and peak traced bytes are read.
- `tracemalloc` omits some native allocations and does not equal formal
  auxiliary space. RSS is not measured.

## Packaging

Docker packaging was optional and was not selected. There is intentionally no
`Dockerfile`; the project needs only a compatible Python interpreter.
