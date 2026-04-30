from livekit.agents.voice import Agent
from livekit.plugins import silero
try:
    a = Agent(instructions="test", stt=None, llm=None, tts=None, vad=silero.VAD.load(), chat_transcription=True)
    print("chat_transcription=True is accepted")
except TypeError as e:
    print(f"chat_transcription=True failed: {e}")
