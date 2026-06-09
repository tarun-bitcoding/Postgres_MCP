from decimal import Decimal
from pathlib import Path

from fastmcp import FastMCP
from fastmcp.server.auth.providers.jwt import JWTVerifier

from database import get_connection, release_connection
from auth_config import ISSUER, AUDIENCE, PUBLIC_KEY_PATH, SERVER_HOST, SERVER_PORT

# --- Authentication ---------------------------------------------------------
# Verify incoming JWTs against our public key. Tokens are minted by
# setup_auth.py using the matching private key.
public_key_path = Path(PUBLIC_KEY_PATH)
if not public_key_path.exists():
    raise SystemExit(
        "Public key not found. Run 'python setup_auth.py' first to create keys."
    )

auth = JWTVerifier(
    public_key=public_key_path.read_text(),
    issuer=ISSUER,
    audience=AUDIENCE,
)

mcp = FastMCP(
    name="Employee Database MCP",
    instructions="""
    This server has a single tool, execute_query, that runs a SQL query
    on the 'employees' table and returns the result.
    """,
    auth=auth,
)

# Schema-changing statements are blocked to protect the database.
FORBIDDEN = ("drop", "truncate", "alter", "create", "grant", "revoke")


def _json_safe(value):
    """Make a database value safe to return as JSON (NUMERIC -> float, etc.)."""
    if isinstance(value, Decimal):
        return float(value)
    return value


@mcp.tool
def execute_query(query: str):
    """
    Run ONE SQL query on the employee database and return the result.

    - SELECT (or anything with RETURNING) -> returns the matching rows.
    - INSERT / UPDATE / DELETE -> changes data and returns how many rows changed.

    Use only the 'employees' table. DROP/TRUNCATE/ALTER/CREATE are not allowed.
    """
    sql = query.strip().rstrip(";").strip()

    if not sql:
        return {"status": "error", "message": "Empty query."}
    if ";" in sql:
        return {"status": "error", "message": "Only one statement is allowed."}

    first_word = sql.split()[0].lower()
    if first_word in FORBIDDEN:
        return {"status": "error",
                "message": f"'{first_word.upper()}' statements are not allowed."}

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql)

            # cur.description is set when the query returns rows
            # (SELECT, or INSERT/UPDATE/DELETE ... RETURNING).
            if cur.description:
                columns = [d[0] for d in cur.description]
                rows = [
                    {col: _json_safe(val) for col, val in zip(columns, record)}
                    for record in cur.fetchall()
                ]
                conn.commit()
                return {"status": "success", "row_count": len(rows), "rows": rows}

            conn.commit()
            return {"status": "success", "affected_rows": cur.rowcount}
    except Exception as e:
        conn.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        release_connection(conn)


if __name__ == "__main__":
    mcp.run(transport="http", host=SERVER_HOST, port=SERVER_PORT)
