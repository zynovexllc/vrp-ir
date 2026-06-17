# Demo asset

`demo.gif` is the terminal demo embedded at the top of the project README. It is
generated deterministically from a committed script — no manual recording, so
anyone (or CI) can reproduce it byte-for-similar.

## Files

- `demo.sh` — the scripted playback (typed commands + real `vrp-ir` output).
- `demo.cast` — the recorded [asciicast](https://asciinema.org) (v2).
- `demo.gif` — the rendered GIF used in the README.

## Regenerate

Requires [`asciinema`](https://github.com/asciinema/asciinema) to record and
[`agg`](https://github.com/asciinema/agg) to render the GIF.

```bash
# from the repo root, with vrp-ir installed (e.g. `pip install -e .`)
asciinema rec --cols 92 --rows 30 -c "bash docs/demo/demo.sh" docs/demo/demo.cast
agg --theme monokai --font-size 16 --idle-time-limit 1.5 --speed 1.1 \
    docs/demo/demo.cast docs/demo/demo.gif
```

The demo only uses the bundled `examples/*.cfg` files and runs fully offline.
