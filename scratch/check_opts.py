import livekit.agents.tts as lk_tts
print(f"APIConnectOptions: {lk_tts.APIConnectOptions}")
try:
    opts = lk_tts.APIConnectOptions()
    print(f"Default APIConnectOptions: {opts}")
except Exception as e:
    print(f"Failed to create default APIConnectOptions: {e}")
