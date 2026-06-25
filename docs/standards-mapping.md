# Advisory standards mapping

`vrp-ir` can attach **advisory** standard references to audit findings. This is a
navigation aid — it connects a finding to a publicly citable control domain so a
reviewer can orient quickly. It is **not** a compliance certification and does
not constitute a regulatory endorsement.

## What a reference is

Each reference (`StandardRef`) carries:

| field | meaning |
| --- | --- |
| `framework` | e.g. `等保` (MLPS), `CIS-style`, `Huawei-hardening` |
| `control` | a **control-domain description** (e.g. "encrypted remote management") — **not** a clause number |
| `level` | for 等保, the grading: `三级` (Level 3) or `四级` (Level 4) |
| `advisory_only` | always `true` |
| `manual_verified` | `true` only after a human verifies the mapping against the standard text |
| `note` | optional |

## 等保 (MLPS) levels

等保 is graded by **level**. **Level 3 (三级)** is the common acceptance bar for
the important systems that typically need an acceptance review (the ICP);
**Level 4 (四级)** applies to critical infrastructure and is stricter. References
record the level so the same check can be cited at the relevant grade.

## Why there are no clause numbers (yet)

We do **not** invent clause numbers. Current references describe the control
**domain** only and are marked `manual_verified: false`. A precise clause
number is added solely after a human verifies it against the published standard
text. Until then, reports render such mappings as *"unverified mapping"*.

## What stays out of the open-source project

Deep, curated 等保 Level 3/4 clause matrices and certification-grade baseline
content are **not** part of `vrp-ir`; they belong to AegisTwin. See
[`ROADMAP.md`](../ROADMAP.md) and [`GOVERNANCE.md`](../GOVERNANCE.md).
