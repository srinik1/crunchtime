"""
Run once to generate VAPID keys for Web Push.
Paste the output into your .env file.

Usage:
    python generate_vapid.py
"""
import base64
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization


def main():
    private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())

    # Private key as PEM — pywebpush expects this format.
    # We compress newlines to \\n so it fits on one line in .env.
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode().strip().replace("\n", "\\n")

    # Public key as uncompressed EC point (65 bytes), base64url-encoded.
    # This is the format browsers expect for applicationServerKey.
    public_key = private_key.public_key()
    public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint,
    )
    public_b64url = base64.urlsafe_b64encode(public_bytes).rstrip(b"=").decode()

    print("Paste these into your .env file:\n")
    print(f"VAPID_PRIVATE_KEY={private_pem}")
    print(f"VAPID_PUBLIC_KEY={public_b64url}")
    print(f"VAPID_EMAIL=mailto:srinikp2@gmail.com")


if __name__ == "__main__":
    main()
