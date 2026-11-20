# Audit target

- Full commit SHA: `9e6125c615ed6ca04154d6ab7a4286e51fea57b0`
- Short SHA: `9e6125c`
- Annotated tag: `lavi-search-audit-v1`
- Source branch: `BLAVI12:lavi/search-algorithms-final`
- Audited path: `Submissions/LaviBen/`

This commit contains the complete runnable project, saved evidence, generated
dashboard, dependency records, and reviewer instructions. Verify the tag and
commit with:

```bash
git rev-parse lavi-search-audit-v1^{commit}
git show --stat --oneline lavi-search-audit-v1
```

Checkout the recorded version without changing it:

```bash
git checkout --detach 9e6125c615ed6ca04154d6ab7a4286e51fea57b0
cd Submissions/LaviBen
python3 -m unittest discover -s tests -v
```

The commit immediately after the audit target changes only this record to add
the resolved SHA. Audit the tagged commit above and follow
`REPRODUCIBILITY.md`; no manual source edits are required.
