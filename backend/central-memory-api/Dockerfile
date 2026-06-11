FROM rust:1.91-bookworm AS builder
WORKDIR /app
COPY Cargo.toml Cargo.lock* ./
COPY src ./src
RUN cargo build --release

FROM debian:bookworm-slim
RUN useradd --system --uid 10001 --home /nonexistent --shell /usr/sbin/nologin memory-api \
    && mkdir -p /data \
    && chown -R memory-api:memory-api /data
COPY --from=builder /app/target/release/central-memory-api /usr/local/bin/central-memory-api
ENV MEMORY_BACKEND_BIND=0.0.0.0:8080 \
    MEMORY_BACKEND_STORAGE_DIR=/data \
    RUST_LOG=info
EXPOSE 8080
VOLUME ["/data"]
USER memory-api
ENTRYPOINT ["/usr/local/bin/central-memory-api"]
