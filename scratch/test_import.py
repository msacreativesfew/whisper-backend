try:
    from livekit.agents.tts.tts import APIConnectOptions
    print(f"Imported from livekit.agents.tts.tts: {APIConnectOptions}")
except ImportError:
    print("Could not import from livekit.agents.tts.tts")

try:
    from livekit.agents.utils import APIConnectOptions
    print(f"Imported from livekit.agents.utils: {APIConnectOptions}")
except ImportError:
    print("Could not import from livekit.agents.utils")
