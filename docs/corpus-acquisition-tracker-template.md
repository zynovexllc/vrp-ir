# Corpus Acquisition Tracker Template

Use this as a simple manual tracker while working `#87`.

Copy this into a private note, Notion page, or issue comment summary as needed.

## Fields

| Field | Meaning |
| --- | --- |
| Contact | Person / team / source |
| Relationship | 1st-degree / 2nd-degree / public / internal |
| Environment | operator / enterprise / lab / integrator |
| Sample target | `vsys`, `aaa`, management plane, unparsed lines, etc. |
| Acquisition level | L0 interview / L1 grammar-only / L2 reduced snippet / L3 assisted reduction / L4 local extractor / L5 private handoff |
| Status | not contacted / asked / replied / blocked / sample promised / sample received / unusable / promoted |
| Risk note | why the contact may be unable to export |
| Next action | exact next step |

## Minimal tracker example

```text
Contact: <name or source>
Relationship: 1st-degree
Environment: operator
Sample target: management-plane / AAA password policy
Acquisition level: L1 grammar-only
Status: asked
Risk note: cannot export topology-bearing config
Next action: follow up in 3 days with the short request template
```

## Promotion states

Use these state meanings consistently:

- `asked` — request sent, no response yet
- `replied` — contact responded, but no artifact yet
- `sample promised` — contact agreed to provide something
- `sample received` — artifact received privately or publicly
- `unusable` — too vague / too risky / too broad
- `promoted` — safely turned into a repo fixture or concrete Phase 2 decision input
