try:
    from livekit.agents.voice import ChatTranscriptionOptions
    print(f"ChatTranscriptionOptions found: {ChatTranscriptionOptions}")
except ImportError:
    print("ChatTranscriptionOptions not found in livekit.agents.voice")

try:
    from livekit.agents import transcription
    print(f"transcription module found: {transcription}")
except ImportError:
    print("transcription module not found")
