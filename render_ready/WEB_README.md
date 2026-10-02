
# Web UI

This repository now includes `web_server.py`, a small browser front-end around
the existing deobfuscator.

## Local setup

Requirements:

- Node.js 18+
- Python 3.10+
- A compatible Luau executable available to the project
- The dependencies required by the existing project

Start:

```bash
python3 web_server.py
```

Open `http://127.0.0.1:8080`.

The UI supports:

- `.lua`, `.luau`, and `.txt` uploads
- devirtualization on/off
- string dumping
- hook disabling
- budget and maximum-run controls
- in-browser result preview
- result download

## Important deployment note

The original engine executes Luau and Python subprocesses and can take minutes
on difficult inputs. It is therefore not a good fit for Vercel-style short-lived
serverless functions. Use a persistent Linux/Windows server, container, VPS,
or another service that permits long-running subprocesses.

For a public deployment, add authentication, upload limits, rate limiting,
per-job timeouts, and preferably a background job queue. Do not expose an
unrestricted arbitrary-code execution service to the public internet.

The web layer does not execute the submitted Lua directly in the browser; it
hands the file to the repository's existing deobfuscation pipeline.
