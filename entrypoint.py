#!/usr/bin/env python3
"""
Entrypoint for single-container registry TLS proxy.
Generates self-signed certs at startup (if not present), starts the registry,
then runs Envoy as PID 1 (TLS on 5001, proxy to registry on 5000).
"""
from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Cert output dir (must match envoy-container.yaml)
CERT_DIR = Path("/etc/envoy/certs")
REGISTRY_BIN = "/bin/registry"
REGISTRY_CONFIG = "/etc/docker/registry/config.yml"
ENVOY_BIN = "/usr/local/bin/envoy"
ENVOY_CONFIG = "/etc/envoy/envoy.yaml"
NGINX_BIN = "/usr/sbin/nginx"
NGINX_CONFIG = "/etc/nginx/nginx.conf"


def generate_certs() -> None:
    try:
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.backends import default_backend
    except ImportError as e:
        print("cryptography not installed:", e, file=sys.stderr)
        sys.exit(1)

    CERT_DIR.mkdir(parents=True, exist_ok=True)
    key_path = CERT_DIR / "tls.key"
    crt_path = CERT_DIR / "tls.crt"
    if key_path.exists() and crt_path.exists():
        return

    key = rsa.generate_private_key(
        public_exponent=65537, key_size=2048, backend=default_backend()
    )
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Registry TLS Proxy"),
        x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
    ])
    import ipaddress
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.utcnow())
        .not_valid_after(datetime.utcnow() + timedelta(days=3650))
        .add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName("localhost"),
                x509.DNSName("registry.local"),
                x509.IPAddress(ipaddress.ip_address("127.0.0.1")),
            ]),
            critical=False,
        )
        .sign(key, hashes.SHA256(), default_backend())
    )
    key_path.write_bytes(
        key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    crt_path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))


def main() -> None:
    generate_certs()

    # Start registry in background (same container)
    reg = subprocess.Popen(
        [REGISTRY_BIN, "serve", REGISTRY_CONFIG],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if reg.poll() is not None:
        sys.exit(2)

    # TLS proxy: Envoy (amd64/arm64) or nginx (armv7; Envoy has no armv7 image)
    if Path(ENVOY_BIN).exists():
        os.execv(ENVOY_BIN, ["envoy", "-c", ENVOY_CONFIG])
    elif Path(NGINX_BIN).exists():
        os.execv(NGINX_BIN, ["nginx", "-c", NGINX_CONFIG])
    else:
        print("No TLS proxy (envoy or nginx) found", file=sys.stderr)
        sys.exit(3)


if __name__ == "__main__":
    main()
