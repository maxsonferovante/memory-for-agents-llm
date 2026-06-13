FROM rust:1.91-bookworm AS builder
WORKDIR /app
COPY Cargo.toml ./Cargo.toml
COPY src ./src
RUN cargo build --release

FROM debian:bookworm-slim
RUN useradd --system --uid 10001 --home /nonexistent --shell /usr/sbin/nologin memory-mcp
COPY --from=builder /app/target/release/memory-mcp-server /usr/local/bin/memory-mcp-server
ENV MEMORY_DATABASE_URL=postgresql://memory:memory@postgres:5432/memory
USER memory-mcp
ENTRYPOINT ["/usr/local/bin/memory-mcp-server"]
