# AAA Password Policy Support Matrix

This matrix is the required analysis artifact for the first manual-grounded
coverage batch.

Rule:

> No parser or audit implementation issue should be opened from this batch
> until this matrix is filled and reviewed.

This is written from the perspective of an offline configuration parser and
acceptance-audit engine. The key question is not "does the command exist?" but:

1. is it **configuration syntax** rather than display/operational syntax,
2. does it appear in saved config text,
3. does it produce a parse-worthy fact,
4. does that fact support an honest offline security judgment.

## Column definitions

| Column | Meaning |
| --- | --- |
| Command family | Canonical command or command family under review |
| Product/doc source | Public source or product family where it is documented |
| View / scope | User view / system view / `aaa` / policy view / display-only |
| Config syntax? | `yes` / `no` / `unclear` |
| Saved-config visible? | Whether this is expected to appear in saved config text consumed by `vrp-ir` |
| Default documented? | Whether public docs state a default behavior clearly enough to rely on |
| Parse-worthy fact | What concrete fact could the IR capture |
| Audit-worthy semantic | What offline acceptance/security semantic this could support |
| Parser-worthy? | `yes` / `no` / `defer` |
| Audit-worthy? | `yes` / `no` / `defer` |
| Risk / ambiguity | What would make implementation unsafe or misleading |
| Decision | `candidate-parser`, `candidate-audit`, `candidate-parser+audit`, `defer`, `drop` |

## Working matrix

| Command family | Product/doc source | View / scope | Config syntax? | Saved-config visible? | Default documented? | Parse-worthy fact | Audit-worthy semantic | Parser-worthy? | Audit-worthy? | Risk / ambiguity | Decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `local-aaa-user password policy administrator` | WLAN AC / Fat AP / Cloud AP command references | AAA view; enters local administrator password policy view | yes | yes (inferred from config-view syntax and display-to-command mapping) | yes, but drift exists: disabled by default in command refs, while some factory-reset notes show enabled state | administrator password-policy control enabled/disabled | do not audit by absence; explicit `undo` would be weak, but defaults/profile drift make absence-based claims unsafe | yes | defer | defaults/profile behavior vary across product generations and factory profiles | candidate-parser |
| `password expire` | WLAN AC / Fat AP / Cloud AP command references | local administrator password policy view | yes | yes (inferred) | yes, but drift exists: default 90 days, some factory profiles 0 days | explicit password validity period in days | explicit `password expire 0` means permanently valid password and is audit-worthy; positive values are hardening evidence | yes | yes | absence is unsafe because documented defaults/factory profiles differ | candidate-parser+audit |
| `password alert before-expire` | WLAN AC / Fat AP / Cloud AP command references | local administrator password policy view | yes | yes (inferred) | yes, but drift exists: default 30 days, some factory profiles 0 days | explicit pre-expiry warning days | explicit `password alert before-expire 0` disables warnings and is audit-worthy | yes | yes | absence is unsafe because factory-profile defaults can suppress prompting without a line in config | candidate-parser+audit |
| `password alert original` | WLAN AC / Fat AP / Cloud AP command references | local administrator password policy view | yes | yes (inferred) | yes; enabled by default in reviewed docs | explicit initial-password-change prompt enabled/disabled | explicit `undo password alert original` disables initial-password-change prompting and is audit-worthy | yes | yes | must key off explicit disabling, not absence | candidate-parser+audit |
| `password history record number` | WLAN AC / Fat AP / Cloud AP command references | local administrator password policy view; local access-user password policy view | yes | yes (inferred) | yes; default 5 historical passwords | password-history depth | explicit `password history record number 0` disables reuse protection and is audit-worthy | yes | yes | semantics are clear, but access-user vs administrator scope must be preserved in IR | candidate-parser+audit |
| `local-aaa-user password policy access-user` | WLAN AC / Fat AP / Cloud AP command references | AAA view; enters local access-user password policy view | yes | yes (inferred from config-view syntax and display-to-command mapping) | yes; disabled by default in reviewed docs | access-user password-policy control enabled/disabled | by itself not a safe check target; it mainly gates access-user-scoped child settings such as history depth | yes | no | access-user branch has narrower child-command set than administrator branch and should not be treated as identical | candidate-parser |
| `user-password complexity-check` | Huawei public command references across multiple product families | AAA view on reviewed docs, but outside the `local-aaa-user ... password policy` view family | yes | yes (inferred) | yes, but conflicting: enabled by default in some WLAN/AP docs, disabled for local users in other Huawei docs | complexity-check enabled/disabled | explicit `undo` could be audit-worthy, but the command model/default semantics drift too much for the first batch | defer | defer | clear cross-product default drift; mixing it into the `local-aaa-user` batch would collapse two command models | defer |
| `local-user password expire` | CX switch-module command references | AAA view; per-local-user command | yes | yes (inferred) | yes; password can be permanently valid (`0`) by default/setting | per-user password expiry days | too identity-specific for a first generic offline acceptance check | defer | no | per-user fact model is different from policy-view controls and may pull IR toward user inventory rather than posture | defer |
| `local-user policy password expire` | CX switch-module command references | AAA view; administrator-only policy on reviewed docs | yes | yes (inferred) | yes; configured password does not expire by default | policy expiry days plus prompt days | explicit no-expiry could be audit-worthy in isolation | defer | defer | different product family and command model from `local-aaa-user`; keep for a later dedicated batch | defer |
| `local-user policy password complexity-enhance` | CX switch-module command references | AAA view | yes | yes (inferred) | yes; disabled by default in reviewed docs | enhanced complexity-check enabled/disabled | potentially audit-worthy, but belongs to the CX `local-user policy` family, not the WLAN/AP `local-aaa-user` family | defer | defer | platform-specific semantics and overlap with `user-password complexity-check` make this a poor first-batch target | defer |
| `display local-aaa-user password policy` | Huawei public command references | display / operational view | no | no | N/A | none for saved-config parser | none directly for offline config parsing | no | no | display-only; should not drive parser scope | drop |

## Outcome from the reviewed matrix

The reviewed command families do **not** form one clean, vendor-wide "AAA
password policy" model.

Instead, they split into at least two materially different implementation
families:

1. `local-aaa-user password policy ...` plus child commands such as
   `password expire`, `password alert before-expire`, `password alert original`,
   and `password history record number` on WLAN AC / Fat AP / Cloud AP docs.
2. `local-user policy ...` and `local-user ... password expire` on CX
   switch-module docs.

That means the first follow-up implementation batch, if opened, must be narrowed
to the first family only.

## Recommended follow-up boundary

If this batch opens a real implementation issue, it should target:

- parsing the `local-aaa-user password policy {administrator|access-user}` view
  family and its child commands,
- preserving administrator vs access-user scope explicitly in IR,
- and auditing only **explicit configured weakening**, not absence-based
  assumptions.

Recommended explicit weakening candidates:

- `password expire 0`
- `password alert before-expire 0`
- `undo password alert original`
- `password history record number 0`

## Required analysis outcome

This matrix is complete only when every row has:

1. a justified `Config syntax?` value,
2. a justified `Saved-config visible?` value,
3. a concrete parser/audit decision,
4. a written ambiguity note where product-family drift or defaults make naive
   implementation unsafe.

## Gate

If more than one command family still has unresolved product/view/default
ambiguity, do **not** open an implementation issue yet. Either:

- narrow the target further,
- or defer this whole family and move to the next candidate area.
