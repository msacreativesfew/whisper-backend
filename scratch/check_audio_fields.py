import livekit.agents.tts as lk_tts
import dataclasses

try:
    fields = dataclasses.fields(lk_tts.SynthesizedAudio)
    print(f"SynthesizedAudio fields: {[f.name for f in fields]}")
except Exception as e:
    print(f"Not a dataclass: {e}")
    import inspect
    print(f"Members: {[m[0] for m in inspect.getmembers(lk_tts.SynthesizedAudio) if not m[0].startswith('_')]}")
