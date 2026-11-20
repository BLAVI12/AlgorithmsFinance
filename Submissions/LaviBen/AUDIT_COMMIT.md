# Audit target

Audit reference: `lavi-search-audit-v1`

The annotated Git tag above identifies the immutable runnable project snapshot.
Resolve and verify its exact commit with:

```bash
git rev-parse lavi-search-audit-v1^{commit}
git show --stat --oneline lavi-search-audit-v1
```

The submission branch also contains a later metadata-only update to this file
that records the resolved full SHA explicitly. Review the tagged commit; do not
edit it before running the commands in `REPRODUCIBILITY.md`.
