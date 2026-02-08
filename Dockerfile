# Single image: registry + Envoy TLS proxy. Certs generated at startup.
# Use Debian base so Envoy (glibc) and registry binary both work.
# Multi-arch: build with --platform (e.g. linux/amd64, linux/arm64). Buildx sets TARGET*.
ARG TARGETOS=linux
ARG TARGETARCH=amd64
ARG TARGETVARIANT=
FROM envoyproxy/envoy:v1.31-latest AS envoy
FROM registry:2 AS registry
FROM debian:bookworm-slim

# Envoy binary (glibc) and registry binary from official images
COPY --from=envoy /usr/local/bin/envoy /usr/local/bin/envoy
COPY --from=registry /bin/registry /bin/registry

# Python for entrypoint (cert generation)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates python3 python3-pip \
    && pip3 install --break-system-packages cryptography \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Registry config
COPY config.yml /etc/docker/registry/config.yml

# Envoy config and entrypoint
COPY envoy-container.yaml /etc/envoy/envoy.yaml
COPY entrypoint.py /entrypoint.py
RUN chmod +x /entrypoint.py && mkdir -p /etc/envoy/certs

# TLS on 5001; registry listens on 5000 inside container
EXPOSE 5001

ENTRYPOINT ["python3", "/entrypoint.py"]
