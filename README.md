# Registry TLS

Local container registry with HTTPS. One Docker image: **registry** behind **Envoy** with TLS on port 5001. Self-signed certs are generated automatically at startup.

- **HTTPS (push/pull):** https://localhost:5001  
- No Docker Compose — build and run a single container.

## Quick start

**From source (repo root):**

```bash
docker build -t registry-tls .
docker run -p 5001:5001 registry-tls
```

**Pre-built image (after CI publishes):**

```bash
docker run -p 5001:5001 ghcr.io/octopilot/registry-tls:latest
```

Clients will see a self-signed cert warning unless you add `"insecure-registries": ["localhost:5001"]` in Docker settings (or trust the cert).

## Persistence

Mount a volume so registry data survives restarts:

```bash
docker run -p 5001:5001 -v registry-data:/var/lib/registry registry-tls
```

## Trusting the certificate (optional)

- **Docker daemon:** Docker Desktop → Settings → Docker Engine (or `/etc/docker/daemon.json`): add `"insecure-registries": ["localhost:5001"]`, then restart Docker. Use only for local dev.
- **macOS:** Add the container’s cert to Keychain and trust for SSL (copy out with `docker cp <container>:/etc/envoy/certs/tls.crt .` first if needed).
- **Linux:** Copy the cert into your system CA store or use `update-ca-certificates`.

## Reuse

- Copy this repo or use the published image from GitHub Container Registry.
- Rebuild when you change Dockerfile, entrypoint, or Envoy config. Certs are generated on each container start if not present; bind-mount `/etc/envoy/certs` to persist or supply your own.
