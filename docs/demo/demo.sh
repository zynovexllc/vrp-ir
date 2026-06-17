#!/usr/bin/env bash
# Demo script played back inside `asciinema rec`. Deterministic, no network.
set -u

PROMPT="\033[1;32m$\033[0m "

type_cmd() {
  printf "%b" "$PROMPT"
  local s="$1"
  for ((i = 0; i < ${#s}; i++)); do
    printf "%s" "${s:i:1}"
    sleep 0.025
  done
  printf "\n"
  sleep 0.4
}

comment() {
  printf "\033[2;37m%s\033[0m\n" "$1"
  sleep 0.8
}

clear
comment "# Huawei VRP/USG config  ->  source-traceable IR + line-cited security audit"
sleep 0.6

type_cmd "vrp-ir parse examples/sample-usg.cfg | python3 -m json.tool | grep -A6 '\"hostname\"'"
vrp-ir parse examples/sample-usg.cfg | python3 -m json.tool | grep -A6 '"hostname"'
sleep 1.4
comment "# ^ every parsed value carries its file:line (provenance)"
sleep 1.2

type_cmd "vrp-ir audit examples/sample-usg-risky.cfg | head -n 29   # top findings"
vrp-ir audit examples/sample-usg-risky.cfg | head -n 29
sleep 0.3
comment "# ...(+2 MEDIUM warnings) -- every finding cites the offending config line"
sleep 2.4

type_cmd "vrp-ir audit examples/sample-usg-risky.cfg --strict ; echo exit=\$?"
vrp-ir audit examples/sample-usg-risky.cfg --strict >/dev/null 2>&1 ; echo "exit=$?"
sleep 0.6
comment "# --strict exits non-zero  ->  drop it straight into CI as an acceptance gate"
sleep 2.4
