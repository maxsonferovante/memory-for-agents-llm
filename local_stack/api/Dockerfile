FROM rust:1.91-bookworm AS builder
WORKDIR /app
COPY Cargo.toml Cargo.lock* ./
COPY src ./src
RUN cargo build --release

FROM debian:bookworm-slim
RUN useradd --system --uid 10001 --home /nonexistent --shell /usr/sbin/nologin memory-api \
    && mkdir -p /data \
    && chown -R memory-api:memory-api /data
COPY --from=builder /app/target/release/local-memory-api /usr/local/bin/local-memory-api
ENV MEMORY_API_BIND=0.0.0.0:8081 \
    MEMORY_DATA_DIR=/data \
    MEMORY_DERIVED_DIR=/data/derived \
    MEMORY_INDEX_PATH=/data/derived/index.json \
    RUST_LOG=info
EXPOSE 8081
VOLUME ["/data"]
USER memory-api
ENTRYPOINT ["/usr/local/bin/local-memory-api"]

