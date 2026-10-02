# Render-ready image for the web wrapper and its Node/Python deobfuscation engine.
FROM debian:bookworm-slim AS luau-builder

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       ca-certificates git cmake make g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
RUN git clone --depth 1 https://github.com/luau-lang/luau.git
WORKDIR /build/luau
RUN cmake -S . -B cmake -DCMAKE_BUILD_TYPE=Release -DLUAU_BUILD_TESTS=OFF \
    && cmake --build cmake --target Luau.Repl.CLI Luau.Ast.CLI --config Release -j2

FROM node:22-bookworm-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=luau-builder /build/luau/cmake/luau /app/bin/luau
COPY --from=luau-builder /build/luau/cmake/luau-ast /app/bin/luau-ast
COPY . /app

RUN chmod +x /app/bin/luau /app/bin/luau-ast /app/deob.js \
    && node --version \
    && python3 --version \
    && /app/bin/luau --version || true

ENV NODE_BIN=node
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/core

EXPOSE 10000
CMD ["python3", "web_server.py"]
