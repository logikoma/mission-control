import sys
sys.path.append('/Users/kleo/Documents/code/openclaw-mumble-bridge')
from openclaw_client import OpenClawClient
import asyncio

async def test():
    client = OpenClawClient(
        gateway_url='http://127.0.0.1:18789',
        gateway_token='4648cfdbb71a0ecf8f9a304c6b7141f03df055045faa290f'
    )
    print("Sending 'Hello'...")
    async for token in client.send_streaming('Hello', speaker='tester'):
        print(token, end='', flush=True)
    print("\nDone.")

if __name__ == "__main__":
    asyncio.run(test())
