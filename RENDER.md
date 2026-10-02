# Deploy on Render

This project is configured as a Render **Web Service** using the included
`render.yaml` Blueprint and `Dockerfile`.

## What the container does

1. Builds the upstream Luau `luau` and `luau-ast` command-line tools for Linux.
2. Installs Node.js and Python.
3. Copies the existing deobfuscation engine into `/app`.
4. Starts `web_server.py`, which binds to `0.0.0.0:$PORT`.
5. Exposes `/health` for Render health checks.

The Linux binaries are built from the official Luau source during the Docker
build rather than attempting to execute the repository's Windows `.exe` files.

## Deploy

Push the repository to GitHub, then create a Blueprint in Render using the
repository. Render will read `render.yaml` and build the Docker image.

You can also create a Web Service manually with:

- Runtime: Docker
- Dockerfile: `./Dockerfile`
- Docker context: `.`
- Health check path: `/health`

No Python package installation step is required because the Docker image
contains the runtime dependencies.

## Production safety

The endpoint executes a deobfuscation pipeline and accepts uploaded source
files. Before making it public, add authentication/rate limiting and keep the
upload and execution limits enabled. Do not expose a general-purpose code
execution endpoint.
