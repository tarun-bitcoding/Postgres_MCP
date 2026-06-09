import os
from dotenv import load_dotenv
from psycopg2.pool import SimpleConnectionPool

load_dotenv()

pool = SimpleConnectionPool(
    minconn=1,
    maxconn=10,
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    database=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
)


def get_connection():
    """Borrow a connection from the pool."""
    return pool.getconn()


def release_connection(conn):
    """Return a connection back to the pool."""
    pool.putconn(conn)
