# Security Policy

## Scope and threat model

`vrp-ir` parses **offline** Huawei VRP/USG configuration text. It performs no
network access and runs no device commands. Two security considerations matter:

1. **It handles sensitive input.** Configuration files can contain IP addresses,
   credentials, SNMP community strings and topology. `vrp-ir` keeps everything
   local and never transmits data anywhere.
2. **It parses untrusted input.** As a config parser it must stay robust — no
   crashes, no unbounded resource use — on malformed or hostile input. Parsing
   bugs that crash or hang on a crafted config are in scope.

## Supported versions

The latest released minor version receives security fixes. Older versions may not.

## Reporting a vulnerability

Please report security issues **privately**:

- Preferred: GitHub **Security Advisories** — go to the repository's **Security**
  tab → **Report a vulnerability**. This opens a private channel with the maintainers.
- Do **not** open a public issue for a vulnerability, and never paste a real config
  that contains live secrets.

We aim to acknowledge a report within **5 business days** and to agree on a
disclosure timeline with the reporter.

## Handling secrets in configs

When sharing a config snippet (e.g. to report a parsing bug), **de-identify it
first** — scrub real IPs, hostnames, keys and community strings. See
[CONTRIBUTING.md](CONTRIBUTING.md) and
[`docs/de-identifying-configs.md`](docs/de-identifying-configs.md). The best bug
reports use minimal, synthetic snippets that reproduce the issue without any
real data.
