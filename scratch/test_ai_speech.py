import asyncio
import os
from livekit import rtc, api
from dotenv import load_dotenv

load_dotenv()

async def main():
    token = api.AccessToken(
        os.getenv("LIVEKIT_API_KEY"),
        os.getenv("LIVEKIT_API_SECRET")
    ).with_identity("test_user").with_name("Tester").with_grants(
        api.VideoGrants(room_join=True, room="friday-room")
    ).to_jwt()

    room = rtc.Room()
    
    @room.on("transcription_received")
    def on_transcription(transcription, participant):
        text = " ".join([s.text for s in transcription])
        print(f"Transcript from {participant.identity}: {text}")

    @room.on("track_subscribed")
    def on_track_subscribed(track, publication, participant):
        print(f"Subscribed to {track.kind} track from {participant.identity}")

    print("Connecting to room...")
    await room.connect(os.getenv("LIVEKIT_URL"), token)
    print("Connected. Waiting for agent to speak...")

    # Wait for a bit to see if agent greets
    await asyncio.sleep(15)
    await room.disconnect()
    print("Disconnected.")

if __name__ == "__main__":
    asyncio.run(main())
