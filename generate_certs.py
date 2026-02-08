#!/usr/bin/env python3
"""
Generate a self-signed TLS certificate for the registry proxy (localhost, registry.local).
Writes tls.crt and tls.key into the local certs/ directory.
Requires: pip install cryptography
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

try:
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.backends import default_backend
except ImportError:
    print("Install the cryptography package: pip install cryptography", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    certs_dir = Path(__file__).resolve().parent / "certs"
    certs_dir.mkdir(exist_ok=True)

    key_path = certs_dir / "tls.key"
    crt_path = certs_dir / "tls.crt"

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048, backend=default_backend())

    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Registry TLS Proxy"),
        x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
    ])
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.utcnow())
        .not_valid_after(datetime.utcnow() + timedelta(days=3650))  # 10 years
        .add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName("localhost"),
                x509.DNSName("registry.local"),
                x509.IPAddress(__import__("ipaddress").ip_address("127.0.0.1")),
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
    print(f"Wrote {key_path} and {crt_path}")


if __name__ == "__main__":
    main()
