# Corpus Acquisition Playbook

This playbook defines how `vrp-ir` should acquire new real-world evidence when
the target environment is security-sensitive and normal "please send us a config
snippet" requests are unrealistic.

This is the expected default for:

- carrier / operator environments,
- regulated enterprise environments,
- customers who cannot export config text,
- samples that still reveal topology even after naïve redaction.

See also [`docs/evidence-source-policy.md`](evidence-source-policy.md), which
defines the repo's allowed evidence-source hierarchy.

## 1. Core principle

In security-sensitive environments, the right question is **not**:

> "Can you send us your config?"

The right question is:

> "What is the smallest grammar- or behavior-level evidence we can safely learn
> without exporting architecture or secrets?"

That shifts the acquisition model from **config export** to **evidence
extraction**.

## 2. What this changes

For these environments, maintainers should assume:

- full config export is usually impossible,
- even de-identified configs may still reveal architecture,
- contributors may be willing to help with behavior reproduction but not with
  raw text export,
- trust is higher when the customer keeps the config local and only emits a
  minimal artifact.

Therefore the acquisition ladder must prefer **zero-export** and
**minimal-export** modes first.

## 3. Acquisition ladder

Use the first level that can produce enough evidence.

## Level 0: Pattern interview (no config export)

Goal:

Learn whether a config family or syntax shape exists in the wild, without
requesting any config lines yet.

Ask for:

- device family / software family (`VRP`, `USG`, etc.),
- command family involved,
- whether the problem is parse failure, missing parse, false negative, or false
  positive,
- whether the syntax is single-line, block-based, multi-view, localized, or
  encoding-sensitive,
- whether the construct is common or rare.

Use when:

- the contact is cautious,
- the security bar is high,
- we are still deciding whether the family is worth targeting.

Result:

- roadmap intelligence,
- but not yet a regression fixture.

## Level 1: Grammar-only line shapes

Goal:

Collect structure without identifiers.

Ask for:

- command skeletons with identifiers replaced by placeholders,
- token order,
- whether the line is top-level or nested inside a view/block,
- whether repeated lines must be merged across views/continuations.

Example:

Instead of:

```text
snmp-agent usm-user v3 ops_team authentication-mode sha ciphertext X privacy-mode aes128 ciphertext Y
```

Ask for:

```text
snmp-agent usm-user v3 <user> authentication-mode <algo> ciphertext <secret> privacy-mode <algo> ciphertext <secret>
```

Use when:

- syntax shape matters more than values,
- the contact cannot export even a reduced real snippet,
- we need to understand parser grammar, not topology.

Result:

- enough to design a candidate parser test,
- still not enough to claim it is a real shipped regression fixture unless a
  maintainer can justify the realism confidently.

## Level 2: Minimal local reduction by the contact

Goal:

The contact locally reduces the config to the smallest reproducer and strips all
identifiers before sending it.

Ask for:

- only the smallest reproducing block,
- placeholders instead of hostnames, IPs, and names,
- notes on expected vs actual behavior.

Use when:

- the contact can safely create a reduced snippet,
- the problem depends on a few lines of surrounding context.

Result:

- strongest path to a public fixture,
- preferred when available.

## Level 3: Maintainer-assisted redaction session

Goal:

The contact does not export raw configs; instead, a maintainer guides them in
real time to derive a safe minimal reproducer.

Mode:

- screen share,
- text-only walkthrough,
- or asynchronous redaction assistance.

Maintainer asks:

- which block is failing,
- what can be replaced with placeholders,
- which surrounding lines are necessary,
- whether architecture-sensitive addressing can be normalized to documentation
  ranges or placeholders.

Use when:

- the contact is willing to help but not willing to send first,
- the syntax is context-heavy,
- the sample needs expert minimization.

Result:

- a safer minimal reproducer,
- often the best path in operator environments.

## Level 4: Customer-side extractor / normalizer

Goal:

Keep the full config local, but run a narrowly-scoped extraction rule on the
customer side to emit only the targeted command family with placeholders.

Examples:

- emit only `user-interface` blocks,
- emit only `aaa local-user` lines,
- emit only `snmp-agent` lines,
- emit only `vsys`-related blocks,
- emit only unparsed lines from a local parser run.

Use when:

- the contact can run a small local helper,
- the environment allows local tooling but not raw export,
- the needed signal is command-family-specific.

Result:

- very high-value evidence with lower disclosure risk.

This is often the best long-term operator strategy.

## Level 5: Full private handoff

Goal:

Only use when the issue is impossible to understand through smaller evidence.

Use when:

- all lower levels failed,
- the contact is explicitly willing to use a private path,
- the sample still cannot be safely reduced without maintainer assistance.

Result:

- high risk / high value,
- should be exceptional, not default.

## 4. What we should ask operator contacts for first

For operator-heavy networks, ask in this order:

1. **unparsed-line families**, not full config sections,
2. **grammar-only command skeletons**,
3. **single-view minimal blocks**,
4. **false negative / false positive reproductions** tied to one check,
5. only then larger context if still necessary.

Rationale:

- this minimizes architecture disclosure,
- increases response rate,
- and is more likely to pass security review on their side.

## 5. What we should never ask for first

Do not start by asking for:

- full config backups,
- "any sample you can share",
- topology-rich routing sections without a specific parser reason,
- raw management-plane configs with live usernames/ACLs/addresses,
- anything that would force the contact to make a security exception.

If the first ask is too expensive or scary, the contact will simply disengage.

## 6. Success criteria for a usable acquisition

A newly acquired artifact is useful if it gives us at least one of:

1. a real syntax pattern we did not understand before,
2. a minimal reproducer for a parser blind spot,
3. evidence that an existing check is missing a real-world case,
4. enough structure to justify building a customer-side extractor for that
   command family.

It is **not** useful enough if it is only:

- a vague statement that "this exists",
- an unverified recollection of syntax,
- a full config we cannot safely commit,
- or a sample too large to attribute the bug.

## 7. Recommended operating strategy right now

Given the current repo state, the best default strategy is:

1. stop assuming contacts will export config,
2. ask first for grammar-only or minimal-block evidence,
3. offer private assisted reduction as the normal path,
4. prepare customer-side extraction as the next support tool if outreach stalls.

In other words:

> **Treat corpus acquisition as a low-export evidence-extraction problem, not a
> config-sharing problem.**

## 8. Implication for `#87`

`#87` should be considered satisfied by the **first sufficiently real,
minimally safe, behavior-reproducing artifact** — not necessarily by a full
traditional config snippet.

If the first usable artifact is:

- a grammar-only skeleton,
- a reduced minimal block,
- or a customer-side extracted command-family sample,

that is enough to evaluate whether a true Phase 2 follow-up should begin.
