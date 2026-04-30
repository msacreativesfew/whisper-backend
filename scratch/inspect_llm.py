import livekit.agents.llm as lk_llm
import inspect

print(f"LLM init signature: {inspect.signature(lk_llm.LLM.__init__)}")
try:
    print(f"LLMCapabilities: {lk_llm.LLMCapabilities}")
except AttributeError:
    print("LLMCapabilities not found in lk_llm")
