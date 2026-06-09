# Employee Database MCP

A small [FastMCP](https://github.com/jlowin/fastmcp) server that exposes simple
tools to manage employee records in PostgreSQL, plus an example client that uses
Google Gemini to pick the right tool from a plain-English question.

## Files

| File             | What it does                                              |
| ---------------- | -------------------------------------------------------- |
| `server.py`      | MCP server with create/get/list/update/delete tools      |
| `database.py`    | PostgreSQL connection pool                                |
| `client.py`      | Example client: Gemini decides which tool to call        |
| `schema.sql`     | Creates the `employees` table                            |
| `.env.example`   | Template for your secrets (copy to `.env`)               |

## Setup

1. Create and activate a virtual environment, then install dependencies:

   ```bash
   python -m venv venv
   venv\Scripts\activate        # Windows
   pip install -r requirements.txt
   ```

2. Copy the env template and fill in your real values:

   ```bash
   copy .env.example .env       # Windows
   ```

3. Create the database table:

   ```bash
   psql -U postgres -d company_db -f schema.sql
   ```

## Run

Start the MCP server:

```bash
python server.py
```

Run the example client (asks Gemini, then calls a tool):

```bash
python client.py
```

## Tools

- `create_employee(name, email, department, salary)`
- `get_employee(employee_id)`
- `list_employees()`
- `update_employee(employee_id, department, salary)`
- `delete_employee(employee_id)`

## Security note

Never commit your real `.env`. It is already listed in `.gitignore`. If a key or
password was ever committed or shared, rotate it.
