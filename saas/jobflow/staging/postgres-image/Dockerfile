FROM golang@sha256:f20d83a83e18dbd2a4714b8ffd4b30b287b6243962dd75608e86abcc63ba4efc AS gosu-builder
WORKDIR /src
RUN git clone --depth 1 --branch 1.20 https://github.com/tianon/gosu.git . \
    && test "$(git rev-parse HEAD)" = "29b939aa5bd4dc588af765b8248f6e39150d2565" \
    && mkdir -p /out \
    && CGO_ENABLED=0 go build -trimpath -ldflags='-s -w' -o /out/gosu .

FROM postgres@sha256:9e2cf6287f25c3151f4c9421ccce2b17f3e60061c111a29165e0d2cdd9ff0a97
COPY --from=gosu-builder /out/gosu /usr/local/bin/gosu
