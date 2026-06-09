CREATE TABLE IF NOT EXISTS employees (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR NOT NULL,
    email       VARCHAR NOT NULL UNIQUE,
    department  VARCHAR,
    salary      NUMERIC,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
