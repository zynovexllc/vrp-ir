# Social preview (OG) card

`og-card.png` (1280×640) is the GitHub **social preview** image — the card shown
when the repo link is shared on GitHub, Hacker News, Reddit, LinkedIn, Slack, etc.
A good card lifts click-through on every shared link.

It is generated deterministically from a committed script (no manual design),
so it stays reproducible and easy to update.

## Regenerate

```bash
python3 docs/og/make_card.py   # writes docs/og/og-card.png
```

Requires `Pillow` and the DejaVu fonts (preinstalled on most Linux). Runs offline.

## Apply it (one manual step)

GitHub has no API for the social preview image, so it must be uploaded once via
the web UI:

> Repo **Settings → General → Social preview → Edit → Upload an image** → choose
> `docs/og/og-card.png`.

After that, re-running the script and re-uploading is all that's needed to refresh it.
