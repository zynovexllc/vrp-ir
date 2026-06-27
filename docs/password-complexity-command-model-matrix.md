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
| Decision | `candidate-parser`, `candidate-audit`, `candidate-parser+audit`, `defer`, `drop` |

## Working matrix

| Command family | Product/doc source | View / scope | Saved-config syntax? | Default documented | Parse-worthy fact | Audit-worthy semantic | Same model as other rows? | Risk / ambiguity | Decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `user-password complexity-check [ three-of-kinds ]` | WLAN/AP-style Huawei command references (for example EDOC1100407658 / EDOC1100363572 class docs) | AAA view | yes | enabled by default in multiple reviewed device-family docs | complexity-check enabled/disabled plus optional strength mode (`three-of-kinds`) | explicit `undo user-password complexity-check` is audit-worthy if scope is preserved; absence is unsafe | no | same command string appears in other docs with different scope/default behavior | candidate-parser+audit |
| `user-password complexity-check [ three-of-kinds ]` | Huawei Wireless Information Center docs stating the command can be configured in AAA or local-AAA scope and applies only to that scope | AAA view or `local-aaa-server` / local-AAA view | yes | reviewed docs say the local-user default can be disabled in local-AAA scope | complexity-check enabled/disabled plus scope (`aaa` vs `local-aaa-server`) | explicit `undo` is still audit-worthy, but only if parser preserves the view scope explicitly | yes, but only within the same command family when scope is modelled | without scope preservation, identical text would collapse conflicting defaults and overstate semantics | candidate-parser+audit |
| `local-user policy password complexity-enhance` | CX-style Huawei command references and related `local-user password` docs | AAA view / `local-user policy` model | yes | disabled by default for local users in reviewed docs | enhanced complexity-check enabled/disabled with stronger semantics and history coupling | explicit disable/enable may be parse-worthy later, but should not be mixed into the first follow-up batch | no | different command name, different default, different policy semantics (uppercase + digits + special chars + previous-10-password restriction) | defer |

## Current interpretation

The reviewed rows currently support a conservative conclusion:

- there is not one clean, repo-wide "password complexity" model
- `user-password complexity-check` and
  `local-user policy password complexity-enhance` should be treated as separate
  command families
- the `user-password complexity-check` family itself still requires explicit
  scope preservation (`aaa` vs `local-aaa-server`)
- conflicting defaults make absence-based auditing unsafe

## Recommended follow-up boundary

A narrowed implementation issue is justified for:

- parsing `user-password complexity-check [ three-of-kinds ]`
- preserving whether the command was configured in `aaa` or `local-aaa-server`
  / local-AAA scope
- auditing only explicit `undo user-password complexity-check`

The following remain out of scope for that follow-up issue:

- `local-user policy password complexity-enhance`
- any absence-based finding that depends on a guessed default
- any attempt to flatten all Huawei password-complexity controls into one
  generic model

## Candidate next outcomes

The next valid outcomes from this matrix are:

1. open a narrowed implementation issue for the `user-password complexity-check`
   family with explicit scope preservation, or
2. keep the CX-style `local-user policy password complexity-enhance` family
   deferred for a later dedicated batch.
