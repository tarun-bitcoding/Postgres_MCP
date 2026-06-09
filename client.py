import os
import json
import asyncio
from pathlib import Path

import google.generativeai as genai
from dotenv import load_dotenv
from fastmcp import Client
from fastmcp.client.auth import BearerAuth

from auth_config import SERVER_URL, TOKEN_PATH

load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GOOGLE_GEMINI_API"))
MODEL = os.getenv("MODEL", "gemini-2.0-flash")
model = genai.GenerativeModel(MODEL)

# Load the JWT created by setup_auth.py and connect over HTTP with it.
token_file = Path(TOKEN_PATH)
if not token_file.exists():
    raise SystemExit("No token found. Run 'python setup_auth.py' first.")

mcp_client = Client(SERVER_URL, auth=BearerAuth(token_file.read_text().strip()))

# Conversation memory: list of "Role: text" lines. Only the last N are sent.
history: list[str] = []
MAX_HISTORY = 12


def build_prompt(question: str) -> str:
    """Ask Gemini to WRITE a SQL query, or answer in words, using memory."""
    recent = "\n".join(history[-MAX_HISTORY:]) or "(no previous messages)"
    return f"""
You are an assistant for a PostgreSQL database.

Table:
  employees(
    id         SERIAL PRIMARY KEY,
    name       TEXT,
    email      TEXT UNIQUE,
    department TEXT,
    salary     NUMERIC
  )

You can do TWO things:

1. If the user wants to add, read, update, delete, count, sort, or analyze data,
   WRITE a single PostgreSQL query that answers it.
   Rules for the SQL:
   - Use ONLY the employees table.
   - Write exactly ONE statement (no semicolons in the middle).
   - Never use DROP, TRUNCATE, ALTER, or CREATE.
   - For INSERT, you may add "RETURNING id".
   - For "highest/lowest/top" use ORDER BY ... LIMIT.

2. Otherwise (greetings, "what can you do", "how many tools/operations",
   general questions), answer the user directly in plain words.
   About yourself: you have ONE tool that runs SQL on the employees table,
   so you can add, view, update, delete, count, sort, and analyze employees.
   Answer such questions helpfully instead of refusing.

Use the conversation so far to understand follow-ups like
"and the lowest one?" or "show me their email".

Conversation so far:
{recent}

New user request:
{question}

Reply with ONLY raw JSON (no markdown, no code fences).

To run a query, use:
{{"action": "query", "sql": "<your SQL>"}}

To answer in words, use:
{{"action": "reply", "text": "<your answer>"}}
"""


def parse_gemini_json(text: str) -> dict:
    """Parse Gemini's reply, stripping ```json fences if present."""
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lstrip().lower().startswith("json"):
            text = text.lstrip()[4:]
    return json.loads(text.strip())


def format_result(data: dict) -> str:
    """Plain-text fallback formatting if the LLM summary is unavailable."""
    if not isinstance(data, dict):
        return str(data)
    if data.get("status") == "error":
        return f"Error: {data.get('message')}"
    if "affected_rows" in data:
        return f"Done. {data['affected_rows']} row(s) affected."

    rows = data.get("rows", [])
    if not rows:
        return "No matching records found."
    # Single value (e.g. a COUNT) -> show it plainly
    if len(rows) == 1 and len(rows[0]) == 1:
        return f"{list(rows[0].values())[0]}"
    # Otherwise show a simple aligned table
    headers = list(rows[0].keys())
    widths = {h: max(len(h), *(len(str(r.get(h, ""))) for r in rows)) for h in headers}
    line = "  ".join(h.ljust(widths[h]) for h in headers)
    sep = "  ".join("-" * widths[h] for h in headers)
    body = "\n".join(
        "  ".join(str(r.get(h, "")).ljust(widths[h]) for h in headers) for r in rows
    )
    return f"{line}\n{sep}\n{body}"


def summarize(question: str, sql: str, data: dict) -> str:
    """Ask Gemini to phrase a friendly answer from the data; fall back to a table."""
    prompt = f"""
The user asked: "{question}"
You ran this SQL: {sql}
The database returned this JSON: {json.dumps(data)}

Write a short, friendly answer in plain English for the user.
- If it is a count, state the number in a sentence.
- If it is a list, present it clearly (a small table or bullet list).
- If data was changed, confirm what happened.
Do NOT show raw JSON. Keep it concise.
"""
    try:
        return model.generate_content(prompt).text.strip()
    except Exception:
        # Quota/error -> still give the user a clean, readable result
        return format_result(data)


async def handle_question(question: str) -> None:
    """Ask Gemini for SQL (with memory), then run it via the execute_query tool."""
    history.append(f"User: {question}")

    try:
        response = model.generate_content(build_prompt(question))
        plan = parse_gemini_json(response.text)
    except Exception as e:
        print(f"LLM error: {e}")
        return

    action = plan.get("action")

    # Plain text answer
    if action == "reply":
        answer = plan.get("text", "(no answer)")
        print(answer)
        history.append(f"Assistant: {answer}")
        return

    # LLM-generated SQL -> run it through the single execute_query tool
    if action == "query":
        sql = plan.get("sql", "").strip()
        if not sql:
            print("Sorry, I couldn't build a query for that.")
            return
        print(f"-> SQL: {sql}")
        try:
            result = await mcp_client.call_tool("execute_query", {"query": sql})
            data = result.data
            answer = summarize(question, sql, data)
            print(answer)
            # Remember the query and its result so follow-ups work.
            history.append(f"Assistant ran SQL: {sql}")
            history.append(f"Result: {json.dumps(data)}")
        except Exception as e:
            print(f"Tool error: {e}")
        return

    print("Sorry, I couldn't understand that.")


async def main():
    print("Employee DB assistant (SQL mode). Type a request in plain English.")
    print("Examples:")
    print("  - add an employee named Riya, email riya@x.com, dept AI, salary 80000")
    print("  - show all employees sorted by salary")
    print("  - who earns the most?")
    print("  - how many people are in the AI department?")
    print("Type 'exit' or 'quit' to stop.\n")

    async with mcp_client:
        while True:
            question = input("you> ").strip()
            if question.lower() in ("exit", "quit"):
                print("Bye!")
                break
            if not question:
                continue
            await handle_question(question)
            print()


if __name__ == "__main__":
    asyncio.run(main())
