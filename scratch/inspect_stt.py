from livekit.plugins import openai as lk_openai
import inspect

print(f"STT init signature: {inspect.signature(lk_openai.STT.__init__)}")
