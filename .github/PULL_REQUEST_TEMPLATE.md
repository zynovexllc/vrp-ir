<!-- Thanks for contributing to vrp-ir! Keep PRs small and focused. -->

## Summary

<!-- What does this PR do and why? Link the issue it closes, e.g. "Closes #12". -->

## Type of change

- [ ] Parser: new construct / fix (Huawei VRP/USG)
- [ ] Audit: new check / fix
- [ ] Docs / examples
- [ ] Build / CI / tooling

## Checklist

- [ ] Tests pass locally: `PYTHONPATH=src python3 -m unittest discover -s tests`
- [ ] **No existing test weakened or deleted** (new tests go in new/extended files)
- [ ] New parsed values carry a **`SourceRef`**, asserted by a test (provenance is the point)
- [ ] No **garbage facts** — a value that can't be parsed cleanly is skipped, not surfaced
- [ ] Core stays **dependency-free**
- [ ] Any config snippet in tests/examples is **synthetic / de-identified** (no real data)
- [ ] Docs / CHANGELOG updated if behavior or surface changed
