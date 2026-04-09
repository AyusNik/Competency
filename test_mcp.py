import asyncio
import httpx

async def run():
    # Test MCP tool directly
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "get_manager_details",
            "arguments": {"user_id": "69d368e103b08348ea7bbcf7"}
        }
    }
    async with httpx.AsyncClient() as client:
        r = await client.post("http://localhost:8003/rpc", json=payload)
        print("Status:", r.status_code)
        print("Response:", r.json())

asyncio.run(run())
