"""Shared JWT auth settings used by the server, the token generator, and client."""

# These must match on both sides (token <-> verifier).
ISSUER = "https://employee-mcp.local"
AUDIENCE = "employee-db-mcp"

# Where the RSA keys and the test token are stored on disk.
PUBLIC_KEY_PATH = "keys/public.pem"
PRIVATE_KEY_PATH = "keys/private.pem"
TOKEN_PATH = "token.txt"

# Token details for local testing.
TOKEN_SUBJECT = "jaydip"
TOKEN_EXPIRES_IN = 3600  # seconds (1 hour)

# HTTP address the server listens on.
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 9000
SERVER_URL = f"http://{SERVER_HOST}:{SERVER_PORT}/mcp"
