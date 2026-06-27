# Password Complexity Command-Model Matrix

This matrix is the required analysis artifact for the next manual-grounded
evidence batch.

Rule:

> No parser or audit implementation issue should be opened from this batch
> until this matrix is filled and reviewed.

The key question is not simply whether Huawei has "a password complexity
command". The key questions are:

1. which product/view family the command belongs to,
2. whether the saved-config syntax is stable enough to parse,
3. whether the documented default is stable enough to support an honest audit,
4. whether two similarly named commands are actually the same model.

## Column definitions

| Column | Meaning |
| --- | --- |
| Command family | Canonical command under review |
| Product/doc source | Public source or product family where it is documented |
| View / scope | AAA view / local AAA view / policy view / other |
| Saved-config syntax? | `yes` / `no` / `unclear` |
| Default documented | What the reviewed public doc says the default is |
| Parse-worthy fact | What the IR could safely capture |
| Audit-worthy semantic | What explicit weakening, if any, could be audited honestly |
| Same model as other rows? | `yes` / `no` / `unclear` |
| Risk / ambiguity | What makes naive implementation unsafe |
| Decision | `candidate-parser`, `candidate-audit`, `defer`, `drop` |

## Working matrix

| Command family | Product/doc source | View / scope | Saved-config syntax? | Default documented | Parse-worthy fact | Audit-worthy semantic | Same model as other rows? | Risk / ambiguity | Decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `user-password complexity-check` | WLAN/AP-style Huawei command references reviewed in the previous batch | AAA view or local AAA view depending doc | yes | enabled by default in multiple reviewed command references | complexity-check enabled/disabled | explicit `undo` could be audit-worthy if the command model is isolated cleanly | unclear | same command name appears with different scope/default wording across docs | defer |
| `user-password complexity-check` | Huawei Wireless Information Center docs reviewed in the previous batch | AAA view / local AAA view with scope-specific behavior note | yes | disabled by default for local users in reviewed docs | complexity-check enabled/disabled, possibly scope-specific | explicit `undo` alone is not enough unless scope/default drift is resolved | no | direct conflict with the enabled-by-default variant; scope interaction may differ by view | defer |
| `local-user policy password complexity-enhance` | CX-style Huawei command references reviewed in the previous batch | AAA view / local-user policy model | yes | disabled by default in reviewed docs | enhanced complexity-check enabled/disabled | explicit absence cannot be audited; explicit enabling/disabling may be parser-worthy | no | different command model and different semantics from `user-password complexity-check` despite overlapping topic | defer |

## Current interpretation

The reviewed rows currently support a conservative conclusion:

- there is not yet evidence for one clean, repo-wide "password complexity"
  model
- `user-password complexity-check` and
  `local-user policy password complexity-enhance` should be treated as separate
  command families unless stronger evidence proves otherwise
- conflicting defaults make absence-based auditing unsafe

## Candidate next outcomes

The next valid outcomes from this matrix are:

1. isolate one product/view family and open a narrowed implementation issue, or
2. keep the whole area deferred and move to a different candidate family.
