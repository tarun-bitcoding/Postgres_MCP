"""
Quick manual test of the MCP tools WITHOUT Gemini.
Run with:  python test_tools.py

It creates an employee, reads it, lists all, updates it, then deletes it.
"""
import asyncio
from fastmcp import Client


async def main():
    client = Client("server.py")
    async with client:
        print("Tools available:", [t.name for t in await client.list_tools()])
        print("-" * 50)

        # 1. Create
        r = await client.call_tool(
            "create_employee",
            {
                "name": "Manual Test",
                "email": "manual_test@example.com",
                "department": "QA",
                "salary": 60000,
            },
        )
        print("create_employee ->", r.data)
        new_id = r.data["employee_id"]

        # 2. Get
        r = await client.call_tool("get_employee", {"employee_id": new_id})
        print("get_employee   ->", r.data)

        # 3. List (bare list -> data is in r.content text)
        r = await client.call_tool("list_employees", {})
        print("list_employees ->", r.content[0].text)

        # 4. Update
        r = await client.call_tool(
            "update_employee",
            {"employee_id": new_id, "department": "DevOps", "salary": 70000},
        )
        print("update_employee->", r.data)

        # 5. Delete (cleanup)
        r = await client.call_tool("delete_employee", {"employee_id": new_id})
        print("delete_employee->", r.data)

        print("-" * 50)
        print("All steps ran. Test row was deleted at the end.")


if __name__ == "__main__":
    asyncio.run(main())
