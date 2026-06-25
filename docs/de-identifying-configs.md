# De-identifying VRP/USG config snippets

Real Huawei VRP/USG snippets are the highest-value bug reports, but production
configs can expose credentials, topology, customer names and security posture.
Share only the smallest synthetic or de-identified snippet that reproduces the
parser or audit behavior.

## What to remove or replace

Before opening an issue or PR, scrub:

- Hostnames, site names, customer names, circuit IDs and device inventory IDs.
- Public and private IPs that reveal real topology. Use documentation ranges:
  `192.0.2.0/24`, `198.51.100.0/24`, `203.0.113.0/24`, or private ranges like
  `10.0.0.0/8` when topology shape matters.
- SNMP communities, passwords, hashes, keys, certificates, AAA/RADIUS/TACACS
  secrets and pre-shared keys.
- Real usernames, domains, email addresses, phone numbers and ticket numbers.
- Provider names, peering ASNs and VPN/customer identifiers.

Preserve only the syntax needed to reproduce the parse or audit issue. If a
value is irrelevant, replace it with a neutral placeholder.

## Safe replacement examples

| Real kind | Use instead |
| --- | --- |
| Hostname/site | `FW-EDGE-01`, `CORE-SW-01`, `SITE-A` |
| Public address | `203.0.113.10`, `198.51.100.20` |
| Internal subnet | `10.10.10.0/24`, `192.168.10.0/24` |
| SNMP community | `public` only when testing weak-community behavior; otherwise `ExampleReadOnly` |
| Password/hash/key | `<redacted-secret>` |
| Customer or circuit name | `CUSTOMER-A`, `CIRCUIT-1` |

## Minimal snippet pattern

Prefer a small reproducer over a full device config:

```text
sysname FW-EDGE-01
#
interface GigabitEthernet0/0/1
 description 上联核心-示例
 ip address 192.0.2.1 255.255.255.0
#
security-policy
 rule name allow-example
  source-zone trust
  destination-zone untrust
  action permit
#
```

Chinese descriptions or rule names are fine when they are synthetic. If the bug
depends on file encoding, mention the encoding explicitly (for example,
GB18030/GBK). Tests can generate non-UTF-8 fixtures at runtime rather than
committing production files.

## Golden corpus convention

When a de-identified snippet becomes a regression fixture:

1. Keep it minimal and synthetic, or document that it was scrubbed.
2. Put reusable fixtures under `tests/fixtures/` when sharing across tests.
3. Add a unit test that asserts the parsed value and its `SourceRef`.
4. For audit fixtures, assert the finding ID, status, severity and evidence line.
5. Never commit full production configs, live secrets or customer-identifying
   topology.

If you are unsure whether a snippet is safe to share, do not post it publicly.
Open a private security advisory or reduce the snippet further until all live
data is gone.
