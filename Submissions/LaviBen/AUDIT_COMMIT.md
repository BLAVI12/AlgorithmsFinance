# Audit target

- Full commit SHA: `f532d3cbb06d9516fac880012840271930990452`
- Short SHA: `f532d3c`
- Annotated tag: `lavi-search-audit-v3`
- Source branch: `BLAVI12:lavi/benchmark-audit-fixes`
- Audited path: `Submissions/LaviBen/`

This commit contains the complete runnable project, saved evidence, generated
dashboard, dependency records, and reviewer instructions after the external
benchmark-audit repairs. Its saved measurements identify clean measurement-code
commit `050bfc846c2860474a348d44858cf29c269e6503`. Verify the tag and target with:

```bash
git rev-parse lavi-search-audit-v3^{commit}
git show --stat --oneline lavi-search-audit-v3
```

Checkout the recorded version without changing it:

```bash
git checkout --detach f532d3cbb06d9516fac880012840271930990452
cd Submissions/LaviBen
python3 -m unittest discover -s tests -v
```

The commit immediately after the audit target changes only this record to add
the resolved SHA. Audit the tagged commit above and follow
`REPRODUCIBILITY.md`; no manual source edits are required.
