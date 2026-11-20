# Phase 2 audit: WelscherYannick

This directory contains Ben Lavi's independent audit of Yannick Welscher's
Phase 1 submission.

- Upstream pull request: <https://github.com/cogeorg/AlgorithmsFinance/pull/23>
- Audited commit: `654516b585dd419ff63f37642d5c211891799fcb`
- Audited path: `Submissions/WelscherYannick/`
- Report: [`AUDIT_REPORT.md`](AUDIT_REPORT.md)
- Executable evidence: [`reproduce_audit.py`](reproduce_audit.py)

The reviewer did not edit the audited checkout. The reproduction script copies
the dashboard to a temporary directory before changing a result value for the
cache test.

## Reproduce

Create Yannick's documented environment in the audited checkout, then run:

```bash
cd Submissions/WelscherYannick
.venv/bin/python -m pytest -p no:cacheprovider -ra

cd ../LaviBen/phase2_welscher_yannick
../../../Submissions/WelscherYannick/.venv/bin/python reproduce_audit.py \
  ../../../Submissions/WelscherYannick
```

The virtual environment may be elsewhere. In that case, invoke
`reproduce_audit.py` with the Python interpreter containing the packages from
Yannick's `requirements.txt`.
