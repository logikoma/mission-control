import sys
sys.path.append('/Users/kleo/Documents/code/openclaw-mumble-bridge')
from tts import TTSClient
import asyncio

async def test():
    client = TTSClient(
        provider="elevenlabs",
        api_key="sk_d32f07264340ae40027cde22db9b4bc9fa290ac2b026fefb",
        elevenlabs_voice_id="pFZP5JQG7iQjIQuC4Bku"
    )
    print("Synthesizing 'Test'...")
    pcm = await client.synthesize("Test")
    if pcm:
        print(f"Success! Got {len(pcm)} bytes of PCM.")
    else:
        print("Failed to synthesize.")

if __name__ == "__main__":
    asyncio.run(test())
