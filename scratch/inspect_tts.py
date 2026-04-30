import livekit.agents.tts as lk_tts
import inspect

print(f"TTS init signature: {inspect.signature(lk_tts.TTS.__init__)}")
try:
    print(f"TTSCapabilities: {lk_tts.TTSCapabilities}")
except AttributeError:
    print("TTSCapabilities not found in lk_tts")
