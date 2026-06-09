"""
One-time / on-demand auth setup for local testing.

Run:  python setup_auth.py

- First run: generates an RSA key pair and saves it under keys/.
- Every run: mints a fresh JWT (signed by the private key) and saves it to
  token.txt, which the client reads to authenticate.

The server only needs the PUBLIC key; the token is signed with the PRIVATE key.
"""
from pathlib import Path

from pydantic import SecretStr
from fastmcp.server.auth.providers.jwt import RSAKeyPair

from auth_config import (
    ISSUER,
    AUDIENCE,
    PUBLIC_KEY_PATH,
    PRIVATE_KEY_PATH,
    TOKEN_PATH,
    TOKEN_SUBJECT,
    TOKEN_EXPIRES_IN,
)


def load_or_create_keys() -> RSAKeyPair:
    """Load the saved RSA key pair, or create and save a new one."""
    public_path = Path(PUBLIC_KEY_PATH)
    private_path = Path(PRIVATE_KEY_PATH)

    if public_path.exists() and private_path.exists():
        return RSAKeyPair(
            public_key=public_path.read_text(),
            private_key=SecretStr(private_path.read_text()),
        )

    public_path.parent.mkdir(parents=True, exist_ok=True)
    key_pair = RSAKeyPair.generate()
    public_path.write_text(key_pair.public_key)
    private_path.write_text(key_pair.private_key.get_secret_value())
    print(f"Generated a new RSA key pair in '{public_path.parent}/'.")
    return key_pair


def main() -> None:
    key_pair = load_or_create_keys()
    token = key_pair.create_token(
        issuer=ISSUER,
        audience=AUDIENCE,
        subject=TOKEN_SUBJECT,
        expires_in_seconds=TOKEN_EXPIRES_IN,
    )
    Path(TOKEN_PATH).write_text(token)
    minutes = TOKEN_EXPIRES_IN // 60
    print(f"Saved a fresh token to '{TOKEN_PATH}' (valid for {minutes} minutes).")
    print("\nThe client reads this token automatically. Token:\n")
    print(token)


if __name__ == "__main__":
    main()
